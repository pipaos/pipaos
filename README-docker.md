## PipaOS Docker

This readme explains how to build pipaOS from a Docker container.

### Setup

From your x86 or ARM based host, build the pipaos Docker image:

```
$ docker build -t pipaos .
```

### Build

Execute the script `build-docker.sh` to test that you can enter the pipaOS shell.
To build pipaOS image, do `build-docker.sh build`.

This should take about 20 minutes on a modest performant computer.
The resulting image will be placed on the current repository directory on the host machine.
