# AMD 镜像构建说明

## 概述
本文档说明如何从AMD提供的原始镜像构建用于sglang项目的DADI镜像。

## 前置条件
- 拥有AMD提供的基础镜像（推荐使用alinux系统）
- 访问阿里巴巴内部Code平台权限
- Docker环境

## 构建步骤

### 步骤1: 获取AMD提供的基础镜像
从AMD团队获取基础镜像，镜像格式通常为：
```
hub.docker.alibaba-inc.com/tre-ai-infra/amd:<tag>
```

### 步骤2: 转换镜像为DADI格式

#### 2.1 检查镜像名称长度
如果镜像名称过长，需要先重新tag为短名称：
```bash
# 示例：原镜像名称过长
docker pull hub.docker.alibaba-inc.com/tre-ai-infra/amd:88b4a10_20260313_containerd_accelerated

# 重新tag为短名称
docker tag hub.docker.alibaba-inc.com/tre-ai-infra/amd:88b4a10_20260313_containerd_accelerated \
           hub.docker.alibaba-inc.com/tre-ai-infra/amd:88b4a10_20260313

# 推送短名称镜像
docker push hub.docker.alibaba-inc.com/tre-ai-infra/amd:88b4a10_20260313
```

#### 2.2 通过CI平台转换镜像
1. 访问CI转换页面：https://code.alibaba-inc.com/alibaba/sglang/ci?createType=yaml&tab=task
2. 选择任务：**转换 DADI 镜像**
3. 在运行配置中填写：
   - **Branch/Tag**: `v0.5.9-amd` (或其他目标分支)
   - **待转换的镜像**: 输入Docker镜像名称（使用短名称）
   - **其他参数**: 保持默认或按需填写
4. 点击运行，等待转换完成
5. 转换成功后，记录生成的DADI镜像名称

### 步骤3: 更新Dockerfile

#### 3.1 切换到目标分支
```bash
git checkout v0.5.9-amd-up_transformers
```

#### 3.2 修改Dockerfile.base镜像
编辑 `docker/ali/Dockerfile.release` 文件，更新FROM语句：

```dockerfile
# 修改前
FROM <旧的镜像名称>

# 修改后
FROM <新转换的DADI镜像名称>
```

示例：
```dockerfile
FROM hub.docker.alibaba-inc.com/tre-ai-infra/amd:88b4a10_20260313_containerd_accelerated
```

#### 3.3 提交更改
```bash
git add docker/ali/Dockerfile.release
git commit -m "Update AMD base image to <新镜像tag>"
git push origin v0.5.9-amd-up_transformers
```

### 步骤4: 验证镜像并记录Commit ID

#### 4.1 进入镜像验证
```bash
# 拉取并运行镜像
docker run -it <DADI镜像名称> /bin/bash

# 在容器内检查代码
cd /opt/sglang
git log -1 --oneline
```

记录当前代码的commit ID，格式类似：`abc1234`

#### 4.2 添加AMD远程仓库
```bash
# 添加AMD远程仓库
git remote add amd https://github.com/zejunchen-zejun/sglang.git

# 验证远程仓库
git remote -v
```

#### 4.3 获取AMD的Qwen3.5分支
```bash
# 获取远程分支
git fetch amd

# 切换到Qwen3.5分支
git checkout -b Qwen3.5_v0.5.9 amd/Qwen3.5_v0.5.9
```

#### 4.4 Rebase操作
```bash
# 确保在Qwen3.5分支上
git branch  # 确认当前在 Qwen3.5_v0.5.9

# Rebase到代码中的commit（使用步骤4.1记录的commit ID）
git rebase <commit_id>

# 处理冲突（如果有）
# 解决冲突后继续
git rebase --continue

# 切换到目标分支
git checkout v0.5.9-amd-up_transformers

# 将Qwen3.5分支rebase到目标分支
git rebase Qwen3.5_v0.5.9

# 推送更新（可能需要force push）
git push origin v0.5.9-amd-up_transformers --force-with-lease
```

## 完整流程示例

```bash
# 1. 拉取并重新tag镜像
docker pull hub.docker.alibaba-inc.com/tre-ai-infra/amd:88b4a10_20260313_containerd_accelerated
docker tag hub.docker.alibaba-inc.com/tre-ai-infra/amd:88b4a10_20260313_containerd_accelerated \
           hub.docker.alibaba-inc.com/tre-ai-infra/amd:88b4a10_20260313
docker push hub.docker.alibaba-inc.com/tre-ai-infra/amd:88b4a10_20260313

# 2. 通过CI平台转换镜像（手动操作）
# 访问: https://code.alibaba-inc.com/alibaba/sglang/ci?createType=yaml&tab=task

# 3. 更新Dockerfile
git checkout v0.5.9-amd-up_transformers
# 编辑 docker/ali/Dockerfile.release，更新FROM语句
git add docker/ali/Dockerfile.release
git commit -m "Update AMD base image"
git push origin v0.5.9-amd-up_transformers

# 4. 验证并rebase
docker run -it <新DADI镜像> /bin/bash
# 在容器内: cd /opt/sglang && git log -1 --oneline
# 记录commit ID，假设为: abc1234

# 退出容器后执行
git remote add amd https://github.com/zejunchen-zejun/sglang.git
git fetch amd
git checkout -b Qwen3.5_v0.5.9 amd/Qwen3.5_v0.5.9
git rebase abc1234
git checkout v0.5.9-amd-up_transformers
git rebase Qwen3.5_v0.5.9
git push origin v0.5.9-amd-up_transformers --force-with-lease
```

## 注意事项

1. **镜像名称长度限制**: CI转换工具对镜像名称长度有限制，过长会导致转换失败，务必使用短名称
2. **Rebase冲突处理**: rebase过程中可能出现冲突，需要手动解决后使用 `git rebase --continue` 继续
3. **Force Push谨慎操作**: 最后一步可能需要force push，确保不会影响其他开发者的工作
4. **Commit ID记录**: 务必准确记录镜像内的commit ID，这是后续rebase的关键
5. **远程仓库验证**: 添加amd远程仓库后，使用 `git remote -v` 确认配置正确
6. **分支保护**: 如果目标分支有保护规则，可能需要临时解除或使用PR方式合并

## 故障排查

### 问题1: CI转换失败
- 检查镜像名称是否过长
- 确认镜像已推送到hub.docker.alibaba-inc.com
- 检查网络连通性

### 问题2: Rebase冲突
```bash
# 查看冲突文件
git status

# 手动编辑解决冲突
# 标记为已解决
git add <conflicted_file>

# 继续rebase
git rebase --continue

# 如果需要中止rebase
git rebase --abort
```

### 问题3: 无法进入镜像
```bash
# 检查镜像是否正确拉取
docker images | grep amd

# 使用不同的entrypoint
docker run -it --entrypoint /bin/bash <镜像名称>
```

## 相关资源

- CI转换平台: https://code.alibaba-inc.com/alibaba/sglang/ci?createType=yaml&tab=task
- AMD远程仓库: https://github.com/zejunchen-zejun/sglang.git
- 项目Dockerfile: `docker/ali/Dockerfile.release`
