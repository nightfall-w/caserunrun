# 建立 python3.9 环境
FROM ccr.ccs.tencentyun.com/library/ubuntu:22.04

# 设置维护者信息
LABEL maintainer="baojun.wang"
RUN cat /etc/os-release
# 设置环境变量 DEBIAN_FRONTEND 为 noninteractive
ENV DEBIAN_FRONTEND=noninteractive
# 设置pip源为国内源

# 更新 apt 源列表
RUN apt-get update && apt-get install -y openssl
COPY docker_build/system/ca-certificates_20230311ubuntu0.22.04.1_all.deb /tmp/ca-certificates_20230311ubuntu0.22.04.1_all.deb
RUN dpkg -i /tmp/ca-certificates_20230311ubuntu0.22.04.1_all.deb
COPY docker_build/system/sources.list /etc/apt/sources.list
RUN apt-get clean all && apt-get update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev tzdata wget curl

# 设置pip源为国内源
COPY docker_build/system/msyh.ttc /usr/share/fonts/
RUN apt-get clean all && apt-get update && apt-get upgrade -y  && apt-get install -y libldap2-dev libsasl2-dev logrotate nginx git vim pkg-config libmysqlclient-dev
COPY docker_build/python/pip.conf /root/.pip/pip.conf

WORKDIR /opt/
RUN wget https://mirrors.huaweicloud.com/python/3.9.9/Python-3.9.9.tgz && \
    tar xzf Python-3.9.9.tgz && \
    cd Python-3.9.9 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall && \
    rm -rf /Python-3.9.9 /Python-3.9.9.tgz \

# 清理已下载的包和依赖
RUN apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# 设置默认Python版本为3.9（注意：这里使用altinstall是为了避免覆盖系统默认的python）
RUN update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.9 1

# 安装pip
RUN python3.9 -m ensurepip

WORKDIR /opt
# 安装java环境
# 下载并安装指定版本的OpenJDK
RUN mkdir /usr/lib/java
RUN wget https://mirrors.huaweicloud.com/openjdk/17/openjdk-17_linux-x64_bin.tar.gz
RUN tar -zxvf ./openjdk-17_linux-x64_bin.tar.gz -C /usr/lib/java

# 设置Java环境变量
ENV JAVA_HOME=/usr/lib/java/jdk-17
ENV JRE_HOME=${JAVA_HOME}/jre
ENV CLASSPATH=.:${JAVA_HOME}/lib:${JRE_HOME}/lib
ENV PATH=${JAVA_HOME}/bin:${PATH}

# 添加java 到系统环境变量
RUN update-alternatives --install /usr/bin/java java /usr/lib/java/jdk-17/bin/java 300

# 下载并安装指定版本的Maven
ENV MAVEN_VERSION 3.9.11
# 下载并解压指定版本的Maven

RUN wget https://mirrors.aliyun.com/apache/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz && \
    tar -xvzf apache-maven-${MAVEN_VERSION}-bin.tar.gz && \
    rm apache-maven-${MAVEN_VERSION}-bin.tar.gz && \
    ln -s /opt/apache-maven-${MAVEN_VERSION} /opt/maven

# 设置Maven环境变量
ENV MAVEN_HOME /opt/maven
ENV PATH $PATH:$MAVEN_HOME/bin

# 将自定义的settings.xml文件复制到Maven的配置目录
COPY docker_build/java/settings.xml /opt/apache-maven-${MAVEN_VERSION}/conf/settings.xml
# 将POM文件复制到容器中
COPY docker_build/java/pom.xml /usr/src/pom.xml
# 设置工作目录
WORKDIR /usr/src
# 安装POM文件中定义的依赖
RUN mvn -s /opt/apache-maven-${MAVEN_VERSION}/conf/settings.xml -B dependency:resolve

# 在容器内/var/www/html/下创建需要的文件夹
RUN mkdir -p /opt/website
RUN mkdir -p /var/logs/celerylog
RUN mkdir -p /data/logs
#ADD ./google-chrome-stable_current_amd64.deb /opt/website/google-chrome-stable_current_amd64.deb
#RUN wget https://repo.debiancn.org/debiancn/pool/main/g/google-chrome-stable/google-chrome-stable_140.0.7339.127-1_amd64.deb
#RUN mv google-chrome-stable_140.0.7339.127-1_amd64.deb /opt/website/google-chrome-stable_current_amd64.deb
ADD docker_build/system/google-chrome-stable_140.0.7339.127-1_amd64.deb /opt/website/google-chrome-stable_current_amd64.deb
ADD docker_build/system/chromedriver /usr/local/bin/chromedriver

# 设置容器内工作目录
WORKDIR /opt/website
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libwayland-client0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        xdg-utils \
    && \
    apt-get install ./google-chrome-stable_current_amd64.deb -y
# 利用 pip 安装依赖
RUN pip3.9 install --upgrade pip
ADD docker_build/python/requirements.txt /opt/website/requirements.txt
RUN pip3.9 install -r requirements.txt

# 将当前目录文件加入到容器工作目录中（. 表示当前宿主机目录）
COPY ../.. /opt/website/engineproxy
WORKDIR /opt/website/engineproxy
RUN mkdir -p logs
RUN touch logs/all.log

RUN rm /root/.gitconfig
RUN git config --global credential.helper store

EXPOSE 8000
EXPOSE 5555

ENV C_FORCE_ROOT true
ENV FLOWER_UNAUTHENTICATED_API true
RUN chmod +x /usr/local/bin/chromedriver
RUN chmod +x ./start.sh

CMD ["./start.sh"]
