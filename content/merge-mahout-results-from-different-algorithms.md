Title: Merge Mahout item based recommendations results from different algorithms
Date: 2014-02-28 18:00
Slug: merge-mahout-recommendations-results-from-different-algorithms
Author: Giovanni Lanzani
Excerpt: Dealing with item-based recommendations does not always yield the expected results. When you combine that with an almost black-box nature of a tool like Apache Mahout, things could quickly go in a direction you don't want them to go.
Template: article
Latex:

Apache [Mahout] is a machine learning library that leverages the power of
[Hadoop] to implement machine learning through the [MapReduce] paradigm. One of
the implemented algorithms is [collaborative filtering][filtering], the most
successful recommendation technique to date. The basic idea behind
collaborative filtering is to analyze the actions or opinions of users to
recommend items similar to the one the user is interacting with.

Memory-based collaborative filtering algorithms can be roughly divided in two categories:
user-based and item-based.

### User-based collaborative filtering

The main idea behind user-based collaborative filtering is that it determines
whether a user is similar to a cluster of users (all similar to each other in
one or another way), and then suggests products based on what the cluster of
users likes. This approach usually employs nearest-neighbors techniques to
determine to which cluster(s) a user belong, and it is the usual choice when
the number of items in the catalogue is much larger than the number of users
(think about Amazon).

### Item-based collaborative filtering

On the other hand, item-based collaborative filtering is used when the number
of users is much larger than the number of items on the catalogue. You could
think of a fast-paced real estate broker, an old-time cars reseller (this is
the example we will use throughout this post), etc.

To determine whether two items are similar, the algorithm analyzes the behavior
of all users that interacted with both items and, after some renormalization,
a similarity measure comes out, say $s_{ij}$, that says how much item $u_i$ is
similar to item $u_j$. It is important to note that the similarity between
$u_i$ and $u_j$ is not based on the products (for example price, color,
intended use), but merely on the interactions that the users had with them.

To make an example: if a lot of users had similar interactions with a Ferrari
[Testarossa], and at the same moment, they would have similar interactions with
a Fiat [500], it would not imply that the two cars are similar (although
they're both Italian): it would show items that are similar according to user
interaction!

### A possible issue with this approach

At GoDataDriven, we had exactly the Testarossa/500 issue at one of our
clients. We would see, in our tests, that cars that were unrelated were ranked
by the system as (very) similar. The way we were invoking Mahout on the input
data was

    :::shell
    mahout itemsimilarity --input $SCORES --output $OUTPUT_PEARSON \
        -s SIMILARITY_PEARSON_CORRELATION

This means that we were using the out-of-the-box [Pearson product moment correlation][pearson]
from Mahout. After having analyzed the input data (which was in the `$SCORES`
folder), we saw something interesting: the Testarossa/500 issue (and many
other similar to that), surfaced because two users (which could have been the
same but with a different IP address) were having exactly the same interactions
with both items.

### Enter the Co-occurrence similarity algorithm

The solution to the problem was quite clear. We had to filter all those
recommendations originated by the interactions of less than $x$ users (later we
set that number to 3). The 'how' turns out to be the interesting part, as it
always is with engineering problems (says a theoretical physicist).

Luckily Mahout can compute similarities with the co-occurrence algorithm, where
the similarity measure is simply given by how many users have interacted with
the two objects, i.e. our $x$! To call Mahout this time we can simply use

    :::shell
    mahout itemsimilarity --input $SCORES --output $OUTPUT_COOCCURRENCE \
        -s SIMILARITY_COOCCURRENCE

### Merging the data

Once we have the output of the two recommendations algorithms, the last step is
to merge the data. We used Hive for the merging process, with the following
script:

    :::sql
    -- Remember that Mahout output is in the form (id1, id2, score)
    CREATE EXTERNAL TABLE cooccurrence_mahout
    (object_id1 BIGINT, object_id2 BIGINT, score FLOAT)
    LOCATION '${env:OUTPUT_COOCCURRENCE}';

    CREATE EXTERNAL TABLE pearson_mahout
    (object_id1 BIGINT, object_id2 BIGINT, score FLOAT)
    LOCATION '${env:OUTPUT_PEARSON}';

    -- The following is a simple join on the first two columns
    CREATE TABLE recommendations
    AS
    SELECT p.object_id1, p.object_id2, p.score, c.score as co-occurrence
    FROM pearson_mahout p
    JOIN cooccurrence_mahout c
    ON p.object_id1 = c.object_id1 and p.object_id2 = c.object_id2;

    -- This table ignores items with low co-occurrence
    CREATE TABLE highly_recommended
    AS SELECT object_id1, object_id2, score FROM recommendations
    WHERE cooccurrence > 2;

### A final note

Running the above script 'as-is' confronted us with yet another quirk: the
joined table, even before deleting items with low co-occurrence and taking care
of the symmetry of the objects id's, was much smaller than the two initial
tables. After a bit of digging, we found out that the default number of items
that Mahout outputs was too low, so that the set scoring high on one algorithm
was not always scoring high when using the other algorithm. To address that
issue we changed the Mahout code to

    :::shell
    mahout itemsimilarity --input $SCORES --output $OUTPUT_PEARSON \
        -s SIMILARITY_PEARSON_CORRELATION --maxSimilaritiesPerItem 100000
    mahout itemsimilarity --input $SCORES --output $OUTPUT_COOCCURRENCE \
        -s SIMILARITY_COOCCURRENCE --maxSimilaritiesPerItem 100000

That's it! I hope that, with this post, you'll be able to get your
recommendations right!

[Mahout]: http://mahout.apache.org
[Hadoop]: http://hadoop.apache.org
[MapReduce]: http://en.wikipedia.org/wiki/Map-reduce
[filtering]: http://en.wikipedia.org/wiki/Collaborative_filtering
[Testarossa]: http://en.wikipedia.org/wiki/Ferrari_Testarossa
[500]: http://en.wikipedia.org/wiki/Fiat_500
[pearson]: http://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient
