Title: Convert chararray user ID's to integers with pig
Date: 2014-01-06 14:00
Slug: convert-chararray-user-ids-to-integer-pig
Author: Giovanni Lanzani
Excerpt: Pig offers an incredibly nice built in function to assign row IDs to data
Template: article

In [a previous
article](|filename|monotonically-increasing-row-ids-with-mapredu.md), Friso
explained how to monotonically increase row IDs with MapReduce. If you read the
article (whose markdown version sports some 1700 words) you may have noticed
that the process it's not straightforward. Thankfully
[pig](http://pig.apache.org), from version 0.11, introduced the
[`RANK`](http://pig.apache.org/docs/r0.12.0/basic.html#rank)
function which allows to do the same in pig with only a handful of lines of
code.

The usefulness of the `RANK` function doesn't end here though. Let's imagine we
need to use the
[`itemsimilarity`](https://cwiki.apache.org/confluence/display/MAHOUT/Itembased+Collaborative+Filtering)
[Mahout](http://mahout.apache.org) algorithm, and all we have is a csv file
where every line is in the form

    user_id, object_id, score

where `user_id` is a `chararray`. Mahout, unfortunately, doesn't accept hashes in this
case, but only integers.

But blindly using the `RANK` function wouldn't cut it: as we know,
`itemsimilarity` computes similarity between objects based on interactions of
users with multiple objects and in this case `RANK` would assign a different
unique id to every `user_id`.

Let's see how we can solve this problem. The desired output is in the form

    integer_user_id, object_id, score

as this is what Mahout loves. The code to accomplish this is

    :::pig
    score = LOAD '/path/to/my/file' AS (user_id:chararray, object_id:int, score:float);

    user = FOREACH score GENERATE user_id;
    unique_users = DISTINCT user;
    new_users = RANK unique_users;

    new_score = JOIN score BY user_id, new_users BY user_id;
    new_score = FOREACH new_score GENERATE rank_unique_users, object_id, score;

    STORE new_score INTO '/path/to/new/file' USING PigStorage(',');

Below we break down block per block how this script works.

The first line loads the file, putting it into `score`. Then

    :::pig
    user = FOREACH score GENERATE user_id;
    unique_users = DISTINCT user;
    new_users = RANK unique_users;

we put into `user` the `user_id` column, and in `unique_users` all distinct
`user_id`'s. This is a crucial step, as we want equal users to have equal
integers id's. The last line of the block add the `rank_unique_user` column
(the name choice is a pig convention) to `new_users`. After that we create
`new_score`

    :::pig
    new_score = JOIN score BY user_id, new_users BY user_id;
    new_score = FOREACH new_score GENERATE rank_unique_users, object_id, score;

through a `JOIN`. The last line basically discards the `user_id` column, as it
is not needed anymore for Mahout purposes. At last we save our file

    :::pig
    STORE new_score INTO '/path/to/new/file' USING PigStorage(',');

which will now have the desired format.
