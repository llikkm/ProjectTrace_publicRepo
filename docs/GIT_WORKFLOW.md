# 日常提交与同步

在项目文件夹内打开终端。默认分支为 `main`，远程为 `origin`。

## 修改前

```powershell
git status
git pull --ff-only
```

有未提交修改时，先处理或保存修改。若拉取提示分支分叉，检查双方提交并正常合并，解决冲突后再推送。

## 修改后

```powershell
git status --short
git diff
git add -- "IMU_Test_261104/IMU_Test_261104.ino"
git diff --cached --stat
git diff --cached
git commit -m "Describe the project update"
git push origin main
```

将 `git add` 后的路径换成此次要提交的具体文件。新增文件也要检查全文，避免上传 Wi-Fi 密码、访问令牌、个人信息或实验参与者资料。

## 检查同步状态

```powershell
git fetch origin
git status --short --branch
git log --oneline -5
```

工作区干净且 `main` 与 `origin/main` 没有 ahead/behind 时，当前修改已同步。

## 公开仓库约定

- 不使用 `git push --force` 或 `--force-with-lease`。
- `.gitignore` 排除本地资料及常见凭据文件；已跟踪文件仍需人工检查。
- 新增 Python 程序时提交源码和依赖清单，排除虚拟环境与缓存。
- 提交前核对作者邮箱。本仓库使用 GitHub noreply 邮箱，配置仅作用于本仓库。
