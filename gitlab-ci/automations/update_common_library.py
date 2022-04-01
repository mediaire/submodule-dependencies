import os
import logging
import gitlab
import re

import yaml
from gitlab.exceptions import GitlabUpdateError
from gitlab_submodule.gitlab_submodule import iterate_subprojects


"""
A script for automatically creating merge requests s to update to the latest
version of a common library. The projects and the assignees/reviewers for each
MR are stored in a `.yml` configuration file.

This script is idempotent: it will only create one open MR at the time
for each project, even if the common library version version changes. In that
case it will update the existing one.
"""


logging.basicConfig(
    format='%(asctime)s %(levelname)s %(module)s:%(lineno)s %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

PRIVATE_GITLAB_TOKEN = os.getenv('PRIVATE_GITLAB_TOKEN')

BASE_DIR = os.path.dirname(__file__)
DESCRIPTION_TEMPLATE = open(os.path.join(BASE_DIR, 'mr_template.txt')).read()


def connect():
    gl = gitlab.Gitlab('https://gitlab.com/',
                       private_token=PRIVATE_GITLAB_TOKEN)
    gl.auth()
    return gl


def create_branch(project,
                  name: str,
                  src_branch: str = 'master',  # where to branch from
                  delete_if_exists: bool = True):
    try:
        branch = project.branches.get(name)
    except Exception:
        branch = None

    if branch:
        if not delete_if_exists:
            return branch
        else:
            branch.delete()
    branch = project.branches.create({'branch': name, 'ref': src_branch})
    return branch


def create_or_update_mr(project,
                        title: str,
                        src_branch: str,
                        reviewer_id: int,
                        dest_branch: str = 'master',
                        description: str = ''):
    mrs = project.mergerequests.list(state='opened', order_by='updated_at')
    mr = None

    for mr_ in mrs:
        if mr_.title == title:
            mr = mr_

    if mr is None:
        mr = project.mergerequests.create({
            'source_branch': src_branch,
            'target_branch': dest_branch,
            'title': title
        })

    mr.reviewer_ids = [reviewer_id]
    mr.assignee_ids = [reviewer_id]
    mr.squash = True
    mr.remove_source_branch = True
    mr.description = description
    mr.save()


def update(project_id, reviewer_id, md_commons_tag_version, commit_sha):
    project = gl.projects.get(id=project_id)
    logger.info(f'id: {project.id} - path: {project.path_with_namespace} ')
    submodules = iterate_subprojects(project, gl)

    if not submodules:
        logger.warning('Project has not submodules, skipping...')
        return
    submodule_map = {submodule.project.name: submodule
                     for submodule in submodules}

    if ('md_commons' not in submodule_map.keys()):
        logger.warning('Project does not have md_commons as a submodule, '
                       'skipping...')
        return

    submodule_path = submodule_map.get('md_commons').submodule.path

    description = DESCRIPTION_TEMPLATE.replace(
        "[Describe what's in this MR]",
        f"(Automatic) Update to md_commons {md_commons_tag_version}"
    )

    branch = create_branch(project=project,
                           name='automatic_update_md_commons',
                           src_branch=project.default_branch)
    create_or_update_mr(project=project,
                        # note: this title should not change, otherwise
                        # we won't find the existing MR
                        title=('[MINOR] '
                               '(Automatic) Update to latest md_commons'),
                        src_branch=branch.name,
                        reviewer_id=reviewer_id,
                        dest_branch=project.default_branch,
                        description=description)

    try:
        project.update_submodule(
            submodule=submodule_path,
            branch=branch.name,
            commit_sha=commit_sha,
            commit_message="Update md_commons",  # optional
        )
    except GitlabUpdateError as e:
        if ' is already at ' in str(e):
            logger.info('MR is already up-to-date')
        else:
            raise e


def list_group_members():
    gl = connect()
    groups = gl.groups.list()
    unique_usernames = set()
    unique_members = []
    # it's probably enough to list members of the root group here
    for group in groups:
        # all=True to include inherited members through ancestor groups
        members = group.members.list(all=True)
        for member in members:
            if member.username in unique_usernames:
                continue
            unique_usernames.add(member.username)
            unique_members.append(member)
    return unique_members


def search_user(pattern: str):
    """basic regexp search in the member names"""
    all_members = list_group_members()
    for member in all_members:
        if re.match(pattern, member.name):
            return member
    raise ValueError('User not found')


if __name__ == '__main__':
    gl = connect()

    common_library = gl.projects.get(id='mediaire/md_commons')

    last_ref = common_library.commits.list(
        ref=common_library.default_branch)[0].id
    last_tag = common_library.tags.list()[0].name

    logger.info(f'common library last tag: {last_tag}, '
                f'last commit hash: {last_ref}')

    with open(os.path.join(BASE_DIR, 'update_common_library_config.yml')) as f:
        projects_to_update = yaml.safe_load(f)['projects_to_update']

    for project_to_update in projects_to_update:
        logger.info(f'Project to update: {project_to_update}')
        reviewer = search_user(project_to_update['reviewer'])
        logger.info(f'Found reviewer {reviewer.name} with id {reviewer.id}')

        update(project_to_update['id'], reviewer.id, last_tag, last_ref)
