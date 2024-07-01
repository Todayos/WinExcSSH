# WinExcSSH

## 配置
修改配置文件 config.config.yml 中的内容，主要包含以下内容

### HostInfo 
> 服务器IP与端口

### UserInfo
> SSH的名用户名与密码

### PceKeys
> 定位进程的关键字，该关键字应该只会查询到同一类服务进程

### TfiifPath
> 启动或停止服务脚本所在的文件路径

### StartCommand
> 启动服务所使用的启动命令

### StopCommand
> 停止服务所使用的停止命令

## 执行
> 执行 python start.py 命令可启动服务
> 
> 执行上述命令前，请确认该包已被添加进python包查找路径