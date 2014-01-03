Title: Monotonically increasing row IDs with MapReduce
Date: 2013-05-30 14:00
Slug: monotonically-increasing-row-ids-with-mapreduce
Author: Friso van Vollenhoven
Excerpt: Apparently a distributed cat -n is more complex than a distributed grep. Here is a way to assign monotonically increasing IDs in MapReduce.
Template: article

Let’s say you have a tab separated file in HDFS, that contains only unique entities, one per line, and you would like to assign a unique ID to each, which also has to be monotonically increasing. So for N records, the IDs should be 0..N-1. Now, if the file is small, you will probably do something very similar to this:

	:::bash
	hadoop fs -cat /some-file.tsv | cat -n | hadoop fs -put - /some-file-with-ids.tsv

(if it’s comma seperated or something else, you’ll probably throw in some awk to fix that)

And we’re done! However, for big files, this is problematic, because all data has to go through one single process on one single machine. Due to the lack of parallelism in this case, the disk or network will be a bottleneck. In this post we’ll show a distributed way of doing this, implemented in Hadoop MapReduce.

### Distributed line numbering

We have some requirements:

- Records are in a file on HDFS and are line separated (1 record per line)
- IDs need to run from 0 to N-1, where N is the number of records
- I want to take advantage of the parallelism (so no job with one single reducer)

So, we really need to have distributed ‘cat -n’. Who’d have though that be more involved than distributed ‘grep’? Anyway, here’s a solution:

1. Run the data through a mapper and have the mapper emit each record AS IS
2. Have each mapper keep track of how may records it sends to each reducer
3. In the cleanup method, have each mapper emit a specialized record for each reducer with the total count of records that it sent to the reducer slot BEFORE that one.
4. Have a specialized partitioner that partitions normal records based on a hash function (that the mappers also must know about in order to keep correct counts) and that partitions the special counter records based on a partition field encoded into the value.
5. Have the framework sort the counter key+value pairs before the records, using a specialized sorting comparator
6. Have the framework group all key+value pairs together, such that each reducer only gets one reduce call using a specialized grouping comparator (that always returns 0)
7. Have each reducer retrieve the count records and accumulate the counts from each mapper it receives
8. Have each reducer emit each record AS IS, prepended by a row ID starting the ID sequence at the number calculated in step 7

So, the trick is to use the mapping phase to build up enough global knowledge about the data set to know exactly how may records there are and how they are partitioned across the reducers. The the framework is used as some sort of giant synchronization barrier and then each reducer will know exactly how many records preceeded its portion of the data.

### Example
Here is an illustrated / pseudo-coded example of the whole process. The job in the example has two mappers and three reducers. The partitioning is based on a fictional hash function that gives the results seen between parentheses. Each mapper keeps an array of counters for keeping track of how many records it sent to each reducer. Note that both the mapper and the partitioner need to know about the hashing function in order to work.

The input file is this:

	ABC (hash == 0)
	DEF (hash == 1)
	GHI (hash == 2)
	JKL (hash == 0)
	MNO (hash == 1)
	------ split ------ (above here goes to mapper 0, below to mapper 1)
	PQR (hash == 2)
	STU (hash == 0)
	VWX (hash == 1)
	YZ0 (hash == 1)

The job will run as follows:

	Mapper 0:
	setup:
	    initialize counters = [0, 0, 0]
	map:
	    input "ABC" ==> emit "ABC", increment counters[0]
	    input "DEF" ==> emit "DEF", increment counters[1]
	    input "GHI" ==> emit "GHI", increment counters[2]
	    input "JKL" ==> emit "JKL", increment counters[0]
	    input "MNO" ==> emit "MNO", increment counters[1]   //now counters == [2, 2, 1]
	cleanup:
	    emit counter for partition 0: none
	    emit counter for partition 1: counters[0] = 2
	    emit counter for partition 2: counters[0] + counters[1] = 4

	Mapper 1:
	setup:
	    initialize counters = [0, 0, 0]
	map:
	    input "PQR" ==> emit "PQR", increment counters[2]
	    input "STU" ==> emit "STU", increment counters[0]
	    input "VWX" ==> emit "VWX", increment counters[1]
	    input "YZ0" ==> emit "YZ0", increment counters[1]   //now counters == [1, 2, 1]
	cleanup:
	    emit counter for partition 0: none
	    emit counter for partition 1: counters[0] = 1
	    emit counter for partition 2: counters[0] + counters[1] = 3

	========================= START SORT / SHUFFLE / MERGE =========================
	The framework sorts all key+value pairs based on the keys. We use a specialized
	comparator that will only make sure that the counters are sorted above the
	actual lines. Also, we use a specialized grouping comparator, that creates only
	one group per reducer, so each reduce method will be called only once, with the
	counters sorted on top and the all the records after that. Scroll down for the
	actual implementation of these.
	========================= END SORT / SHUFFLE / MERGE ===========================

	Reducer 0:
	reduce:
	    initialize offset = 0
	    input "ABC" ==> emit "offset <tab> ABC", increment offset   //emits 0<tab>ABC
	    input "JKL" ==> emit "offset <tab> JKL", increment offset   //emits 1<tab>ABC, and so on...
	    input "STU" ==> emit "offset <tab> STU", increment offset   //last emitted offset is 2 from here

	Reducer 1:
	reduce:
	    initialize offset = 0
	    input counter with value 2 ==> offset = offset + 2
	    input counter with value 1 ==> offset = offset + 1  //now offset == 3
	    input "DEF" ==> emit "offset <tab> DEF", increment offset   //emits 3<tab>DEF
	    input "MNO" ==> emit "offset <tab> MNO", increment offset   //emits 4<tab>MNO, and so on...
	    input "VWX" ==> emit "offset <tab> VWX", increment offset
	    input "XY0" ==> emit "offset <tab> XY0", increment offset   //last emitted offset is 6 from here

	Reducer 2:
	reduce:
	    initialize offset = 0
	    input counter with value 4 ==> offset = offset + 4
	    input counter with value 3 ==> offset = offset + 3  //now offset == 7
	    input "GHI" ==> emit "offset <tab> GHI", increment offset   //emits 7<tab>GHI
	    input "PQR" ==> emit "offset <tab> PQR", increment offset   //emits 8<tab>PQR

Resulting will be this:

	0   ABC
	1   JKL
	2   STU
	3   DEF
	4   MNO
	5   VWX
	6   XY0
	7   GHI
	8   PQR

> Note that the ordering of records was not preserved in the process. The job will re-order the records arbitrarily. If the result needs to be sorted in some way, then there’s the solutions of pre-sampling of the data and doing total order partitioning (just like the terasort example). In order for this to work, the mappers also would need to know about the partition boundaries that the total ordering partitioner uses.

### Code
There are two source files: [RowNumberJob.java](https://github.com/friso/graphs/blob/master/job/src/main/java/nl/waredingen/graphs/misc/RowNumberJob.java) and [RowNumberWritable.java](https://github.com/friso/graphs/blob/master/job/src/main/java/nl/waredingen/graphs/misc/RowNumberWritable.java). The former is the job (with mapper and reducer implementations) and the latter is the writable implementation used for intermediate values and the partitioner. Below is a brief comment on some of the moving parts.

### Implementation
The implementation of this job has three special parts (other than a mapper and reducer implementation):

1. A custom partitioner
2. A custom grouping comparator
3. A custom writable to use as value in the intermediate data

### Partitioner
In Hadoop, the partitioner can base its partitioning decision on both the key and the value at hand. We make convenient use of this fact, by partitioning on the value. If the value is a counter record, we look at the given partition (set in the mapper code). If the value is a actual record, we partition based on the hash of the record. The hashing logic is also export from the partitioner (as a static method), such that the mapper code can use the same logic to determine which counters to increment.

### Sorting
If you have been paying attention, you know that I rely on sorting to make sure that the counter records go on top. Now in order to make sure this happens, we don’t need to implement anything special. We just emit the counter records with a key that sorts before the key we use for value records. In this case, we use a standard ByteWritable, with the values ’T' for counter and ‘W’ for value (the Dutch will understand).

### Grouping Comparator
Since we emit the counter records only once from the mapper, we receive them only once on the reducer side. Each reducer will only just emit whatever it receives in terms of actual data records. Hence, there is no point in grouping things. Remember that we use the key to make the distinction between counters and actual records (we need to in order to sort the counters on top). If we didn’t create a custom grouping comparator, the counters and actual values would appear as two different groups in the reducer. In order to get everything into one group, we implement a comparator that always return 0 (meaning everything is equal).

### Performance
We read all the data, write it back in a different order, push most of it through the network and then read and write it once more. This is a lot of trouble just to do line numbering. Is it really worth it? See these results:

**Input size 1.45GB** *==> cat wins*

Pipe through cat: 0m23s
MapReduce: 0m33s (50 mappers, 3 reducers)

**Input size 145GB** *==> MapReduce wins*

Pipe through cat: 44m03s
MapReduce: 7m36s (2633 mappers, 80 reducers)

This test was run on a 16 node cluster with 12 disks/node, 32GB RAM, 1Gb NICs. No fancy tuning was done apart from some basics. Input and output were uncompressed, intermediate data was compressed with the Snappy codec. The pipe through cat test was done from the master node of the cluster and was bound by using only a single disk at a time.
