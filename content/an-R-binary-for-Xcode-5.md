Title: An R binary for Xcode 5
Date: 2013-10-18 14:00
Slug: an-R-binary-for-Xcode-5
Author: Giovanni Lanzani
Excerpt: With Xcode 5.0 being released exactly one month ago (September, the 18th), some may have noticed that installing packages from source in R.app (which can be downloaded at The Comprehensive R Archive Network) does not work anymore. In fact R complains that the command llvm-gcc-4.2 is not found.
Template: article

With Xcode 5.0 being released exactly one month ago (September, the
18th), some may have noticed that installing packages from source in `R.app`
(which can be downloaded at [The Comprehensive R Archive Network](http://cran.r-project.org/bin/macosx))
does not work anymore. In fact R complains that the command `llvm-gcc-4.2`
is not found.

The culprit lies in Xcode 5.0, not shipping `llvm-gcc-4.2` anymore. `R.app`
only accepts that compiler as it is the one
used to build the version of `R.app` mentioned above.

But lo and behold, recompiling `R.app` with Xcode 5.0 fixes it: the nice folks
at [GoDataDriven](http://www.godatadriven.com) (Us!) compiled a new version
that you can download
[here](/static/resources/R_and_framework.zip). Once
downloaded, move `R.app` into your `/Applications` folder and move
`R.framework` in `/Library/Frameworks` (may require authentication).

Double clicking the new `R.app` should open an Xcode 5.0 friendly R: enjoy!


