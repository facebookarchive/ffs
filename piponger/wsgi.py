#! /usr/bin/python3
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from main import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5003)
