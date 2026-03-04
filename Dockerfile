# CaseRunRun Dockerfile
# 基于Ubuntu 22.04 LTS
FROM ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV VENV_ROOT=/opt/venv
ENV PYENV_ROOT=/opt/pyenv
ENV JAVA_HOME=/usr/lib/jvm
ENV MAVEN_HOME=/opt/maven
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$MAVEN_HOME/bin:$PATH"

# 复制系统安装包
COPY docker_build/system/ /tmp/system/

# 先使用Ubuntu默认源安装ca-certificates
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 使用本地sources.list
RUN cp /tmp/system/sources.list /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    unzip \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libffi-dev \
    zlib1g-dev \
    liblzma-dev \
    tk-dev \
    libncurses5-dev \
    libncursesw5-dev \
    openjdk-8-jdk \
    openjdk-11-jdk \
    openjdk-17-jdk \
    maven \
    python3-venv \
    python3-pip \
    direnv \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libappindicator1 \
    libindicator7 \
    fonts-liberation \
    xdg-utils \
    libasound2 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libfreetype6 \
    libgcc1 \
    libglib2.0-0 \
    libgtk2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    fonts-liberation \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装Chrome浏览器
RUN dpkg -i /tmp/system/google-chrome-stable_140.0.7339.127-1_amd64.deb || apt-get -f install -y

# 安装Chrome驱动
RUN chmod +x /tmp/system/chromedriver && \
    mv /tmp/system/chromedriver /usr/local/bin/

# 安装字体
RUN mkdir -p /usr/share/fonts/truetype/msyh && \
    cp /tmp/system/msyh.ttc /usr/share/fonts/truetype/msyh/ && \
    fc-cache -f -v

# 设置pyenv的Python构建镜像源
ENV PYTHON_BUILD_MIRROR_URL=https://registry.npmmirror.com/-/binary/python
ENV PYTHON_BUILD_MIRROR_URL_SKIP_CHECKSUM=1

# 安装pyenv
RUN git clone https://github.com/pyenv/pyenv.git $PYENV_ROOT \
    && cd $PYENV_ROOT && src/configure && make -C src

# 安装Python版本
RUN pyenv install 3.8.10 && \
    pyenv install 3.9.10 && \
    pyenv install 3.10.4 && \
    pyenv install 3.11.0 && \
    pyenv global 3.9.10

# 配置Java替代方案
RUN update-alternatives --install /usr/bin/java java /usr/lib/jvm/java-8-openjdk-amd64/bin/java 100 && \
    update-alternatives --install /usr/bin/java java /usr/lib/jvm/java-11-openjdk-amd64/bin/java 200 && \
    update-alternatives --install /usr/bin/java java /usr/lib/jvm/java-17-openjdk-amd64/bin/java 300 && \
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-8-openjdk-amd64/bin/javac 100 && \
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-11-openjdk-amd64/bin/javac 200 && \
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-17-openjdk-amd64/bin/javac 300

# 安装Maven
ENV MAVEN_VERSION=3.9.11
RUN wget -q https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz && \
    tar -xzf apache-maven-${MAVEN_VERSION}-bin.tar.gz -C /opt && \
    ln -s /opt/apache-maven-${MAVEN_VERSION} $MAVEN_HOME && \
    rm apache-maven-${MAVEN_VERSION}-bin.tar.gz

# 创建虚拟环境根目录
RUN mkdir -p $VENV_ROOT && chmod 777 $VENV_ROOT

# 创建项目目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 配置pip源
# COPY docker_build/python/pip.conf /etc/pip.conf

# 配置Maven设置
RUN mkdir -p /etc/maven
COPY docker_build/java/settings.xml /etc/maven/settings.xml

# 安装项目依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 安装测试报告生成工具
RUN pip3 install pytest-polymeric-report

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]