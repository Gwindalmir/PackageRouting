import sys

from utilities.Logger import Logger
sys.path.append("..")



class HashSet:
    """Implementation of a HashSet with chained buckets.
       Worst case complexity is O(N), best case is O(1)."""
    def __init__(self, buckets):
        super().__init__()
        self.buckets = []

        # Initialize the buckets to empty lists
        for _ in range(buckets):
            self.buckets.append([])

    def __find_bucket_number(self, hash_):
        bucket = hash_ % len(
            self.buckets)  # Compute the bucket with modulo of the bucket count
        Logger.log(Logger.LogLevel.DEBUG,
                   f"Hash {hash} maps to bucket {bucket}")
        return bucket

    def __find_bucket_for_item(self, item):
        hashcode = hash(item)  # get unique hash of the object
        Logger.log(Logger.LogLevel.DEBUG,
                   f"Hash is {hashcode} for item {item}")
        bucket_number = self.__find_bucket_number(
            hashcode)  # get the bucket number mapped to the hash
        bucket = self.buckets[
            bucket_number]  # get the bucket it should be added to
        return (bucket, bucket_number)

    def add(self, item):
        """Adds a new item to the HashSet."""
        (bucket, bucket_number) = self.__find_bucket_for_item(
            item)  # Get bucket item will be added to
        # Check if bucket already has item
        try:
            if bucket.index(item):
                # already contains item
                Logger.log(Logger.LogLevel.DEBUG,
                           f"Bucket {bucket_number} already contains {item}")
        except (IndexError, ValueError):
            Logger.log(Logger.LogLevel.DEBUG,
                       f"Adding {item} to bucket {bucket_number}")
            bucket.append(item)  # add item to the bucket

    def remove(self, item):
        """Removes an item from the HashSet."""
        # Getting the bucket is an O(1) operation
        (bucket, bucket_number) = self.__find_bucket_for_item(
            item)  # Get bucket item should belong to
        Logger.log(Logger.LogLevel.DEBUG,
                   f"Removing {item} from bucket {bucket_number}")
        # Iterating over the bucket to remove the item is an O(N) operation
        # If the HashSet has no collisions, it's O(1)
        bucket.remove(item)

    def contains(self, item):
        """Checks if the HashSet contains the specified item."""
        (bucket, _) = self.__find_bucket_for_item(item)

        # Iterating over the bucket is an O(N) operation
        # If the HashSet has no collisions, it's O(1)
        for i in bucket:
            if i == item:
                return True
        return False

    def clear(self):
        """Empties the HashSet."""

        # Empties all the buckets, this is O(N^2)
        for b in self.buckets:
            b.clear()

    def search(self, key):
        # This is a support method for the iterator
        # Returns the bucket given a key (which is really the index)
        bucket_number = self.__find_bucket_number(key)
        bucket = self.buckets[
            bucket_number]  # get the bucket it should be added to
        return bucket

    def __iter__(self):
        """Iterates over the HashSet contents."""
        # While this appears to be an O(N^2) operation,
        # It's actually O(1), since an iterator only returns the next item
        # and each item is retrieved in O(1) time
        for v in range(len(self.buckets)):
            current_bucket = self.search(v)

            for i in current_bucket:
                yield i

    def __len__(self):
        length = 0
        # This counts all the items currently stored in the HashSet
        # This is O(N)
        for b in self.buckets:
            length += len(b)
        return length

    def __str__(self):
        result = "Buckets: " + str(len(self.buckets)) + "\n"
        for b in range(len(self.buckets)):
            result += "Bucket " + str(b) + ": " + repr(self.buckets[b]) + "\n"

        return result

    def __repr__(self):
        result = ""
        for b in range(len(self.buckets)):
            result += f"{repr(self.buckets[b])} \n"

        return result
