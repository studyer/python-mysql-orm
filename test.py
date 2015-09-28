#!/usr/bin/env python
# -*- coding:utf-8 -*-
from model.writer import Writer

__author__ = 'studyer'

if __name__ == "__main__":
    writer = Writer()
    # writer.save()
    writer.find_by_id(65)
    print writer.Name
