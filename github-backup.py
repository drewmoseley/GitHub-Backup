#!/usr/bin/env python

# Author: Anthony Gargiulo (anthony@agargiulo.com)
# Created Fri Jun 15 2012

import pygithub3
from argparse import ArgumentParser
import os
import sys
import subprocess

def main():
   # A sane way to handle command line args.
   # Now actually store the args
   parser = init_parser()
   args = parser.parse_args()
   args.backupdir = args.backupdir.format(username=args.username)
   args.gistsdir = args.gistsdir.format(username=args.username, backupdir=args.backupdir)

   try:
      user = run(['git', 'config', 'github.user'])
   except Exception:
      user = None

   try:
      password = run(['git', 'config', 'github.password'])
   except Exception:
      password = None

   try:
      token = run(['git', 'config', 'github.token'])
   except Exception:
      token = None

   if not user:
      user = os.environ.get('GITHUB_USER', os.environ.get('GITHUB_USER'))

   if not password:
      password = os.environ.get('GITHUB_PASSWORD', os.environ.get('GITHUB_PASSWORD'))

   if not user:
      sys.exit("Unable to determine github username, please set github.user or export GITHUB_USER")

   if not password:
      sys.stderr.write("Unable to determine github password. To access private repositories, set github.password or export GITHUB_PASSWORD\n")
      user = None

   # Make the connection to Github here.
   gh = pygithub3.Github(login=user, password=password, token=token)

   # Get all of the given user/org's repos
   try:
      repos = gh.repos.list_by_org(args.username).all()
   except pygithub3.exceptions.NotFound:
      repos = None

   if not repos:
      repos = gh.repos.list(args.username).all()

   for repo in repos:
      clone(repo.clone_url, os.path.join(args.backupdir, repo.name), name=repo.full_name, mirror=args.mirror)

   for gist in gh.gists.list(args.username).all():
      clone(gist.git_pull_url, os.path.join(args.gistsdir, gist.id), quiet=args.cron, mirror=args.mirror)

def init_parser():
   """
   set up the argument parser
   """
   parser = ArgumentParser(
   description="makes a backup of all of a github user's repositories")
   parser.add_argument("username", help="A Github username, default to GITHUB_USER or LOGNAME")
   parser.add_argument("-b", "--backupdir", default="./{username}",
         help="The folder where you want your backup repos to go (Default: %(default)s)")
   parser.add_argument("-g", "--gistsdir", default="{backupdir}/gists",
         help="The folder where you want your gist backup repos to go (Default: %(default)s)")
   parser.add_argument("-c","--cron", help="Use this when running from a cron job",
      action="store_true")
   parser.add_argument("-m","--mirror", help="Use the --mirror option when cloning",
      action="store_true")
   return parser


def run(cmd):
    stdout, stderr = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
    return stdout.rstrip()


def clone(url, destdir, quiet=False, name=None, mirror=False):
   if name is None:
      name = os.path.basename(url)

   if quiet:
      git_args = "-q"
   else:
      print("Processing {}".format(name))
      git_args = ""

   if mirror:
      git_args += " --mirror"

   if os.path.exists(destdir):
      if not quiet:
         print("Updating existing repo at {}".format(destdir))
      os.system('cd {} && git pull {}'.format(destdir, git_args))
   else:
      if not quiet:
         print("Cloning {} to {}".format(url, destdir))
      os.system('git clone {} {} {}'.format(git_args, url, destdir))

   if mirror:
      if not quiet:
         print("Updating server info in {}".format(destdir))
      os.system('git update-server-info')

if __name__ == "__main__":
   main()

# vim: set et fenc=utf-8 sts=3 sw=3 :
