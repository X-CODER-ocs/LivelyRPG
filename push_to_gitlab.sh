#!/bin/bash
# 推送到 GitLab 镜像仓库
# 使用方式: GITLAB_TOKEN=你的令牌 ./push_to_gitlab.sh

set -e

GITLAB_REPO="https://X_CODER-ocs:${GITLAB_TOKEN}@gitlab.com/X_CODER-ocs/LivelyRPG.git"

echo "=== 推送到 GitLab ==="

# 检查是否已添加 gitlab 远程
if ! git remote get-url gitlab &>/dev/null; then
    git remote add gitlab "$GITLAB_REPO"
    echo "已添加 GitLab 远程仓库"
else
    git remote set-url gitlab "$GITLAB_REPO"
    echo "已更新 GitLab 远程仓库 URL"
fi

git push gitlab main

echo "=== 完成 ==="