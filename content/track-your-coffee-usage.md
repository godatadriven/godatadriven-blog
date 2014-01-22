Title: Track your coffee usage with google docs and python
Date: 2014-01-22 09:30
Status: draft
Slug: track-your-coffee-usage-with-google-docs-and-python
Author: Giovanni Lanzani
Excerpt: Being data driven not only means analyzing financial results, building recommendations system or deploy Hadoop clusters: sometimes it means answering simple questions as: "When will we need to order new Nespresso?"
Template: article
Latex:

Recently at GoDataDriven we purchased some Nespresso capsules. For each
of the following aromas we ordered 5 boxes (10 capsules per box):

+ Dharkan (my personal favorite!);
+ Decaffeinato Intenso;
+ Vivalto Lungo;
+ Roma;
+ Volluto;
+ Rosabaya.

One of the nice thing of being a data driven organisation is that data can be
almost anything you deal with, Nespresso included. That is why I started
analysing our Nespresso usage (on a box level, i.e. with a 10 capsules
granularity) with two questions in mind:

1. When will aroma *x* finish?
2. How many capsules of aroma *x* do we drink?

The results are publicly [accessible][] (shown are only the aromas of which we
drank at least 10 capsules since restocking). In this post I'll walk you
through the process of building something similar.

## The theory

Let us suppose that we restocked on a certain day (let's call it day 0). The
restock meant that we bought 5 boxes of Dharkan as that was finished. After 1
day we finish the first box. Naively we would think that after 4 days Dharkan
will finish.

The next box, however, lasts 3 days. The one after that lasts, again, three
days. How can we predict when the coffee will be over?

To answer that we can use [linear regression], an approach to, in our
case, describe coffee consumption as time passes. Very bluntly put, linear
regression helps draw a line describing past data points and, hopefully,
predicting future data point.

In the figure below we show exactly that: the little crosses are our past data
points, while the line indicates the "best" fit for the crosses.

<figure class="embed-top hide-smooth dark">
    <img src="static/images/dharkan_linear.png"
        alt="A linear fit of Dharkan Nespresso boxes">
    <figcaption>
        A linear fit of Dharkan Nespresso boxes
    </figcaption>
</figure>

The line in the picture can also be mathematically expressed with the following
equation:


$$
D_{harkan} = 4.9 - 0.49 \times d_{ays}
$$

Which basically says that the number of Dharkan boxes is 4.9 minus the number
of days since the last restock multiplied by 0.49. So if we had restocked 6
days ago, the line predicts that only 2 boxes are left (more or less).

After ten days instead we get out of coffee :)

$$
D_{harkan} = 4.9 - 0.49 \times 10 = 4.9 - 4.9 = 0
$$

Below we can visually see when panic spreads at the office.

<figure class="embed-top reveal-smooth dark">
    <img src="static/images/dharkan_panic.png"
        alt="A linear fit of Dharkan Nespresso boxes, with some panic going on">
    <figcaption>
        After 10 days the panic spreads at the office as Dharkan slowly
        finishes.
    </figcaption>
</figure>

Of course having more (or less) data points changes the fit. Using only the
first two data points, we'd be screaming every Friday, as you can see in the
picture below.

<figure class="embed-top reveal-smooth dark">
    <img src="static/images/early_fit.png"
        alt="A linear fit of Dharkan Nespresso boxes, but with only two data
        points">
    <figcaption>
        You can almost feel the Nespresso machine grinding away.
    </figcaption>
</figure>

Ok, so now we know how to do regression. Let's see if we can make something
through which we can let everybody know when we run out of coffee, so they can
order it for us.

## The data structure

[accessible]: http://s.lanzani.nl/coffee_gdd "Coffee"
[linear regression]: https://en.wikipedia.org/wiki/Linear_regression "Linear regresssion"
