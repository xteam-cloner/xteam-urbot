# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

FROM theteamultroid/ultroid:main

# set timezone
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY installer.sh .

RUN bash installer.sh

# the basic requirements.
RUN apt-get install -y ffmpeg python3-pip curl
RUN python3 -m pip install -U pip

# install nodejs.
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs

COPY . .

# changing workdir
WORKDIR "/root/TeamUltroid"

# start the bot.
CMD ["bash", "startup"]
