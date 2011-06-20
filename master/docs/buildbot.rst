\input texinfo @c -*-texinfo-*- @c %**start of header @setfilename
buildbot.info @include version.texinfo @settitle BuildBot Manual -
@value{VERSION} @defcodeindex cs @defcodeindex sl @defcodeindex bf
@defcodeindex bs @defcodeindex st @defcodeindex bc @defcodeindex dv @c %**end
of header

@c these indices are for classes useful in a master.cfg config file @c
@csindex : Change Sources @c @slindex : Schedulers and Locks @c @bfindex :
Build Factories @c @bsindex : Build Steps @c @stindex : Status Targets @c
@dvindex : Developer Reference

@c @bcindex : keys that make up BuildmasterConfig

@c Output the table of the contents at the beginning. @contents

Introduction
************

@include introduction.texinfo

Installation
************

@include installation.texinfo

Concepts
********

@include concepts.texinfo

.. _configuration:

Configuration
*************

@include configuration.texinfo

Customization
*************

@include customization.texinfo

Command-line Tools
******************

@include cmdline.texinfo

Resources
*********

@include resources.texinfo

Developer Information
*********************

@include developer.texinfo

@unnumbered Index @printindex cp

@bye