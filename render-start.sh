#!/usr/bin/env bash
export PATH="${PATH}:/opt/render/project/.render/chrome/opt/google/chrome/"
gunicorn app:server