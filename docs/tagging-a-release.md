# Tagging a new Docker release

> **This process is upstream's (`BrightID/BrightID-Node`), not this fork's.** A
> `docker` tag exists on `upstream` but not on `origin` (this repo,
> `Meta-Node/BrightID-Aura-Node`), and no `docker` *branch* was found on either
> remote — only the tag, on upstream. Step 2 below (`git checkout --track
> origin/docker`) assumes a `docker` branch exists to track; that may have been
> consolidated away since this was last written, or `origin` in the original
> instructions meant upstream's origin, not this fork's. Aura-node doesn't yet
> have its own documented release-tagging process — this page is ported as
> historical reference for upstream's process, not a verified aura-node
> workflow. Treat step 2 as unconfirmed until someone validates it against
> upstream directly.

Steps 1-4 are done on your local machine with a key for pushing to `origin:master` on GitHub.

1. Update the `master` branch.
```
git checkout master
git pull
```
2. Merge the latest changes to release files into the `docker` branch.
```
git checkout --track origin/docker
git checkout master docker-compose.yml config.env web/brightid-nginx.conf web/index.html
git commit -m "Describe what was changed"
git push
```
3. Delete the old `docker` tag.
```
git tag -d docker
git push origin :refs/tags/docker
```
4. Create a new `docker` tag.
```
git tag docker
git push origin --tags
```

Step 5 is done on the GitHub website.

5. Publish the release.
     1. Go to https://github.com/BrightID/BrightID-Node/releases
     1. Edit the release. (Click "Edit")
     1. Publish the release. (Click "Publish release")
