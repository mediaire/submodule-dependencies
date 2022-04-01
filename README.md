# Submodule Dependencies

Supplementary material for the [PyCon '22][pycon_22] Talk [_Quitting pip: How
we use git submodules to manage internal dependencies that require fast
iteration_][pycon_talk].

At [medi**ai**re][mediaire] we use git submodules to distribute internal
dependencies across projects. This repository shows you how we use it in our
Docker workflow and provides some useful CI automations.


## Project Structure Example

You can find a basic example for the submodule structure in the directory
`project/`.

To setup the submodule structure like this, run the following commands. This
adds the submodule under the `_`-prefixed path and
```bash
git submodule init
git submodule add git@github.com:mediaire/mediaire_toolbox.git _mediaire_toolbox
ln -s _mediaire_toolbox/mediaire_toolbox mediaire_toolbox
```

As a user of the already created repository, you simply have to run
```bash
git submodule init && git submodule update
```
to set it up. Please note that `git submodule update` has to be run after
checking out a different ref, like a branch or a tag.

If you want to run the demo Docker container that showcases how everything
ties together, simply run
```bash
make
```
and it will do all the setup and image building for you. You need to have
Docker installed.


## CI Automations

We use Gitlab to host our code, so these automations are targeted at gitlab-ci,
but it should be pretty straight forward to port them to Github or Travis.


### Check Submodule Refs

Performs a check and only exits successfully (exit code 0) if all the
submodules in the folder are pointing to a valid version tag. It also exits
successfully if there are no submodules.

A "good" version is one that follows [_Semantic Versioning_ (SemVer)][semver],
i.e., `x.y.z`.

If the environment variable `ALLOW_DIRTY_SUBMODULES` is defined, it always
returns exits with code 0.

In [`gitlab_ci/.gitlab-ci-template.yml`](./gitlab-ci/.gitlab-ci-template.yml)
you can find an example configuration for Gitlab CI. It will execute the
script [`gitlab_ci/automations/check_submodule_refs.py`
](./gitlab-ci/automations/check_submodule_refs.py) at every attepted merge or
tag.


### Update Common Library
A script for automatically creating merge requests s to update to the latest
version of a common library. The projects and the assignees/reviewers for each
MR are stored in a `.yml` configuration file.

This script is idempotent: it will only create one open MR at the time
for each project, even if the common library version version changes. In that
case it will update the existing one.

In this current version, the one common library is hardcoded, but it is rather
trivial to generalize the solution. To run the script, simply execute `make`
in `gitlab_ci/`. This can be automated on Gitlab CI using the provided
[`gitlab_ci/.gitlab-ci.yml`](./gitlab_ci/.gitlab-ci.yml) configuration. It will
setup a scheduled job.

The configuration file
[`gitlab_ci/automations/update_common_library_config.yml`
](./gitlab_ci/automations/update_common_library_config.yml) lists the Gitlab
repository ID and the name of the target assignee for that project. Freeform
is fine, we use the search API to find the account ID by name in the current
group's members.


[pycon_22]: https://semver.org/
[pycon_talk]: https://2022.pycon.de/program/B3HC8S/
[mediaire]: https://www.mediaire.de/
[semver]: https://semver.org/
