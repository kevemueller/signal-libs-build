#!/usr/bin/env python3

import json
import pprint
import os
import sys

print(sys.argv)
libs_ver = {}
libs_ver["libclient"] = sys.argv[1]


libs = {
        #"zkgroup": {
            # zkgroup is included in libsignal-client v0.10.0, and is no longer a dependency in libsignal-service-java
            #"repo": "signalapp/zkgroup",
            #"jar_name": "zkgroup-java",
            #"filename": "zkgroup",
            #},
        "libclient": {
            "repo": "signalapp/libsignal-client",
            "jar_name": "signal-client-java",
            "filename": "signal_jni",
            "cargo-flags": "-p libsignal-jni",
            },
        }

hosts = {
        "linux": {
                "runner": "ubuntu-18.04",
                "lib-prefix": "lib",
                "lib-suffix": ".so",
                "triple": "x86_64-unknown-linux-gnu",
                "install-cmd": "sudo apt-get update && sudo apt-get install",
                },
        "macos": {
                "runner": "macos-latest",
                "lib-prefix": "lib",
                "lib-suffix": ".dylib",
                "triple": "x86_64-apple-darwin",
            },
        #"macos-aarch64": {
                #"runner": "macos-11",
                #"lib-prefix": "lib",
                #"lib-suffix": ".dylib",
                #"triple": "aarch64-apple-darwin",
                    ## macos-11 runner uses x86-64 processers.
                    ## Using a cross target aarch64-apple (below)
            #},
        "windows": {
                "runner": "windows-latest",
                "lib-suffix": ".dll",
                "triple": "x86_64-pc-windows",  # no "-msvc" because static lib, see next line
                "install-cmd": "choco install",
                "req-pkg": "nasm",  # req for boringssl
                "rust-flags": "-C target-feature=+crt-static",
                        # Static linking to remove MSVC dependendency.
                        # zkgroup/ffi/node/Makefile
                        # libsignal-client/node/build_node_bridge.py
            },
        }

cross_targets = [
        {
            "target": "aarch64-unknown-linux-gnu",
            "req-pkg": "gcc-aarch64-linux-gnu g++-aarch64-linux-gnu",
            "linker": "aarch64-linux-gnu-gcc",
            "build-env-vars": "CC=aarch64-linux-gnu-gcc CXX=aarch64-linux-gnu-g++ CPATH=/usr/aarch64-linux-gnu/include",
                #https://github.com/signalapp/libsignal/issues/482#issuecomment-1220896664
        },
        {
            "target": "armv7-unknown-linux-gnueabihf",
            "req-pkg": "gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf",
            "linker": "arm-linux-gnueabihf-gcc",
            "build-env-vars": "CC=arm-linux-gnueabihf-gcc CXX=arm-linux-gnueabihf-g++ CPATH=/usr/arm-linux-gnueabihf/include RUST_BACKTRACE=1",
        },
        {
            "target": "i686-unknown-linux-gnu",
            "req-pkg": "gcc-i686-linux-gnu g++-i686-linux-gnu",
            "linker": "i686-linux-gnu-gcc",
            "build-env-vars": "CC=i686-linux-gnu-gcc CXX=i686-linux-gnu-g++ CPATH=/usr/i686-linux-gnu/include",
        },
        {
            "target": "aarch64-apple-darwin",
            "host": {
                "runner": "macos-11",
                "lib-prefix": "lib",
                "lib-suffix": ".dylib",
            },
        },
    ]


matrix = {
        "lib": [],
        "host": [],
        "cross": [None],
        "include": [],
        }


for lib_name, lib_dict in libs.items():
    if not libs_ver[lib_name]:
        continue
    lib_dict["name"] = lib_name
    lib_dict["ref"] = libs_ver[lib_name]
    matrix["lib"].append(lib_dict)

matrix["host"] = list(hosts.values())

target_to_host = {"linux": "linux", "apple": "macos"}
for cross in cross_targets:
    try:
        host = cross.pop("host")
    except KeyError:
        for target_partial_name, host_name in target_to_host.items():
            if target_partial_name in cross["target"]:
                host = hosts[host_name]
                break
    for lib in matrix["lib"]:
        matrix["include"].append(
                {
                    "lib": lib,
                    "host": host,
                    "cross": cross,
                }
            )

if not matrix.get("host"):
    matrix = {"include": matrix["include"]}
    jobs_total = len(matrix["include"])
else:
    jobs_total = 1
    for jobs_num in (len(key_array) for key, key_array in matrix.items() if key != "include"):
        jobs_total *= jobs_num
    jobs_total += len(matrix["include"])
print("Total num of jobs:", jobs_total)

pprint.pprint(matrix)

j = json.dumps(matrix)
gh_output_file = os.environ["GITHUB_OUTPUT"]
with open(gh_output_file, 'a') as gh_out:
    gh_out.write(f"matrix={j}\n")

