# Run like the following:
# docker build --target rpm --output rpmbuild/ .
#
FROM centos:7 AS build
MAINTAINER Professional Services: Software Services <eos-cs-sw@arista.com>

RUN yum -y update && yum clean all
RUN yum -y install epel-release
# Install packaging dependencies
RUN yum -y install \
  which \
  git \
  wget \
  make \
  rpm-build

WORKDIR /src
COPY . .

RUN make rpm

FROM scratch AS rpm
COPY --from=build /src/rpmbuild/burstmonitor-*.rpm /
