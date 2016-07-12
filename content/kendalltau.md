Title: Using Kendall's tau to compare recommendations
Date: 2016-07-12 15:00
Slug: kendall-tau-recommendations
Author: Rogier van der Geer
Excerpt: How to use Kendall's tau to compare recommendations.
Template: article
Latex:

<span class="lead">Kendall's tau is a rank correlation metric, used to compare the order of two lists.</span>

## Intro

The [Kendall Tau](https://en.wikipedia.org/wiki/Kendall_rank_correlation_coefficient) is a metric that can be used to compare the order of two ranks.

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

So we have two concordant pairs and four discordant pairs. This means that in the end, $\tau = \frac{2-4}{15} = -\frac{1}{3}$.
