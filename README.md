# SHUM PropTech RSS Mirror

Daily snapshot mirror of two public RSS feeds that SHUM's Technology Intelligence cloud
routine ("⚡ PropTech Sources daily monitor") needs to read but cannot reach directly —
the routine's cloud sandbox only permits egress to a small allowlist of domains
(github.com, npmjs.org, pypi.org, and similar), and rejects arbitrary sites like
`techcrunch.com` and `rightmove.blog` outright (`EGRESS_BLOCKED`, confirmed 2026-09-03).

A GitHub Action here (`.github/workflows/mirror.yml`) fetches both feeds daily at
05:45 UTC — 25 minutes before the routine runs at 06:10 UTC — and commits them to
`feeds/` only when their content actually changed. The routine then clones this repo
(a plain public GitHub repo, same access pattern as `matterport/developer-docs` and
`antonkomarev/github-trending-archive`, which it already reads successfully) and runs
`git log --since='25 hours ago'` against these two files, exactly like it does for the
Matterport SDK changelog.

## Mirrored sources

- `feeds/techcrunch-proptech.xml` ← https://techcrunch.com/tag/proptech/feed/
- `feeds/rightmove-techblog.xml` ← https://rightmove.blog/feed/

## Why public

The mirrored content is already fully public (RSS feeds of published news/blog posts) —
there is nothing here to keep private. Public also means the routine can `git clone`
this repo with zero credentials, avoiding the need to store a GitHub token inside the
cloud routine's configuration. GitHub Actions minutes are free and unlimited on public
repositories regardless of account plan, so this costs nothing and doesn't touch any
other repo's private-repo minutes quota.

## Manual run

`workflow_dispatch` is enabled — trigger a run any time from the Actions tab, or:

```
gh workflow run mirror.yml --repo tradeshum/shum-proptech-rss-mirror
```
