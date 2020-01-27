# Copyright 2020 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Common functions for the ``ovsdb-subordinate`` interface classes"""

import hashlib


def hash_hexdigest(s):
    """Hash string using SHA-2 256/224 function and return a hexdigest

    :param s: String data
    :type s: str
    :returns: hexdigest of hashed data
    :rtype: str
    :raises: TypeError
    """
    if not isinstance(s, str):
        raise TypeError
    return hashlib.sha224(s.encode('utf8')).hexdigest()
