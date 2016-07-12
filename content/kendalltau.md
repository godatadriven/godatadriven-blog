Title: Using Kendall's tau to compare recommendations
Date: 2016-07-12 15:00
Slug: kendall-tau-recommendations
Author: Rogier van der Geer
Excerpt: How to use Kendall's tau to compare recommendations.
Template: article
Latex:

<span class="lead">Kendall's tau is a rank correlation metric, used to compare the order of two lists.</span>

## Intro

The [Kendall Tau](https://en.wikipedia.org/wiki/Kendall_rank_correlation_coefficient) is a metric that can be used to compare the order of two ranks. It is defined as

$$\tau \equiv \frac{n_c - n_d}{n(n-1)/2},$$

where:

$$
\begin{align}
    n &= \text{the length of the lists},
    n_c &= \text{the number of concordant pairs},
    n_d &= \text{the number of discordant pairs}.
\end{align}
$$

Let's have a look at an example:
```python
a = ['apple', 'pear', 'banana', 'kiwi']
b = ['banana', 'pear', 'kiwi', 'apple']
```
Here we have six pairs of words:

- `('apple', 'pear')` is _discordant_ (swapped),
- `('apple', 'banana')` is _discordant_,
- `('apple', 'kiwi')` is _discordant_, 
- `('pear', 'banana')` is _discordant_,
- `('pear', 'kiwi')` is _concordant_ (in the same order),
- `('banana', 'kiwi')` is _concordant_.

So we have two concordant pairs and four discordant pairs. This means that in the end, $\tau = \frac{2-4}{6} = -\frac{1}{3}$.

## Comparing recommendations

A problem arises when one tries to compare recommendations. A recommender often comes up with a _very_ long list of all possible items, while we are only interested in a few items at the top. 

For example, a recommender of a webshop will rank all products that are available in the shop, and then show the best (let's say top-5) as suggestions. If we want to compare the output of two recommenders we are not interested in the correlation of the _entire_ ranks, since only the 5 best results are shown.

One would want to compare only the top-5 results of each recommender. The problem here lies in the fact that the Kendall tau is undefined if the two ranks do not contain the same elements. And if we are comparing two recommenders which each pick 5 items from a very large set, then it is likely that there are some items that do not occur is both lists, if not all.

## 
