# GitHub Actions 自动部署配置

## 配置说明

本项目已配置GitHub Actions自动部署，当代码推送到main或master分支时，将自动部署到服务器。

## 部署前准备

在使用自动部署前，需要在GitHub仓库中配置以下Secrets：

1. `HOST` - 服务器IP地址
2. `USERNAME` - 服务器用户名
3. `SSH_KEY` - 服务器SSH私钥（用于无密码登录）

## 配置步骤

1. 在GitHub仓库页面，点击 `Settings` 选项卡
2. 在左侧菜单中选择 `Secrets and variables` -> `Actions`
3. 点击 `New repository secret` 按钮
4. 添加以下Secrets：
   - `HOST`: 您的服务器IP地址 (例如: 121.43.119.155)
   - `USERNAME`: 服务器登录用户名 (例如: root 或其他用户)
   - `SSH_KEY`: 服务器SSH私钥内容

## 部署流程

1. 当代码推送到main/master分支时触发
2. 自动拉取最新代码到服务器
3. 安装Python和Node.js依赖
4. 重启所有服务

## 服务说明

自动部署将启动以下服务：
- 订阅服务 (subscribe.py) - 端口 5001
- 发布服务 (publish.py) - 端口 5000
- 数据分析服务 (data_address.py) - 端口 5002
- 通用后端服务 (app.py) - 端口 3000
- 前端服务 (Vite dev server) - 端口 5173

## 注意事项

- 确保服务器上已安装Python 3.10+和Node.js 16+
- 确保服务器防火墙开放相应端口
- 首次部署前需要手动启动前端服务（如果需要）

## 故障排除

如果部署失败，请检查以下内容： 

1. **GitHub Secrets配置**：
   - 确认 `HOST`、`USERNAME`、`SSH_KEY` 已正确配置
   - 检查SSH密钥格式是否正确

2. **服务器连接**：
   - 确认服务器IP地址可访问
   - 确认SSH密钥有正确权限

3. **首次部署**：
   - 首次部署时，脚本会自动克隆代码到服务器
   - 确认服务器有足够权限执行相关操作