# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import threading
import unittest
from typing import Any, List, Tuple

import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

from batch_inference import batching
from batch_inference.batcher import Batcher


class Gpt2Batcher(Batcher):
    def __init__(self) -> None:
        super().__init__()
        self.pad_token = [0]

    def batch(self, requests: List[Tuple]) -> Tuple[List[Tuple], Any]:
        """Batch multiple M requests into 1 batched requests
        Pad and concat input_ids from predict method, and create attention_masks based on input_ids

        Args:
            requests: a list of M requests, each request is a tuple of input_id

        Returns:
            batched requests: a list of 1 batched requests, each batched request is a tuple of input_ids and attention_masks
            context for unbatch: will be passed to unbatch method
        """
        lengths = [len(request[0]) for request in requests]
        max_len = max(lengths)
        input_ids = []
        attention_masks = []
        # pad input id and create attention mask
        for request in requests:
            ids = request[0]
            pad_len = max_len - len(ids)
            input_id = ids + pad_len * self.pad_token
            attention_mask = [1] * len(ids) + [0] * pad_len
            input_ids.append(input_id)
            attention_masks.append(attention_mask)
        return [input_ids, attention_masks], None

    def unbatch(self, batched_responses: List, unbatch_ctx: Any) -> List:
        """Unbatch 1 batched responses into M responses
        batched_responses is already a list of M responses, return it directly
        """
        return batched_responses


# eos_token = 50256   # Token of <|endoftext|>
eos_token = 13  # Token of .  Use for debugging


@batching(batcher=Gpt2Batcher(), max_batch_size=4)
class Gpt2Model:
    def __init__(self):
        self.model = GPT2LMHeadModel.from_pretrained("gpt2")
        self.max_output_length = 64
        self.eos_token = eos_token

    def predict_batch(self, input_ids, attention_masks):
        past_key_values = None
        length = len(input_ids)
        input_ids = torch.tensor(input_ids)
        attention_masks = torch.tensor(attention_masks)
        results = []
        for i in range(length):
            results.append([])

        processing = list(range(length))

        for i in range(self.max_output_length):
            output = self.model(
                input_ids,
                attention_mask=attention_masks,
                past_key_values=past_key_values,
                use_cache=True,
            )
            past_key_values = output.past_key_values
            # Simply take token with max prod as generated token
            logits = output.logits[..., -1, :]
            tokens = torch.argmax(logits, dim=1)

            tokens = tokens.tolist()
            finished = []
            for i, actual_index in enumerate(processing):
                results[actual_index].append(tokens[i])
                if tokens[i] == eos_token:
                    finished.append(i)

            if finished:
                finished.reverse()
                # Delete finished requests
                for index in finished:
                    del processing[index]
                    del tokens[index]
                    past_key_values = self.delete_index_past_key_values(
                        past_key_values, index
                    )
                    attention_masks = torch.cat(
                        [attention_masks[:index], attention_masks[index + 1 :]]
                    )
            if not processing:
                break

            # input_ids will contain generated token id, while attention_masks contains historical masks
            input_ids = torch.tensor(tokens, dtype=torch.int32).unsqueeze(1)
            new_mask = torch.ones(len(processing), dtype=torch.int32).unsqueeze(1)
            attention_masks = torch.cat([attention_masks, new_mask], dim=1)

        return results

    def delete_index_past_key_values(self, past_key_values, index):
        # Shape: (layer, k&v, [batchsize, head, token length, head dim]), for example: (12, 2, [batchsize, 12, n, 64]) for GPT2 small
        deleted = []
        for i, layer in enumerate(past_key_values):
            deleted.append([])
            for tensor in layer:
                deleted[i].append(torch.cat([tensor[:index], tensor[index + 1 :]]))
            deleted[i] = tuple(deleted[i])
        return tuple(deleted)


class TestModelHost(unittest.TestCase):
    def setUp(self) -> None:
        self.model_host = Gpt2Model.host()
        self.model_host.start()

    def tearDown(self) -> None:
        self.model_host.stop()

    def test_simple(self):
        text = "The Manhattan bridge"
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        input_ids = tokenizer.encode(text)
        output_ids = self.model_host.predict(input_ids)
        result = tokenizer.decode(output_ids)
        self.assertTrue(len(result) > 0)

    def test_concurrent(self):
        def send_requests():
            texts = [
                "The Manhattan bridge",
                "Python lists are a data structure similar to dynamically",
                "Tuples in Python are a data structure used to store multiple elements in a single variable. Just like list data structure, a tuple is",
                "Even though List and Tuple are different data structures",
                "An operating system (OS) is the program that",
                "An operating system brings powerful benefits to computer software",
                "As long as each application accesses the same resources and services",
                "An operating system provides three essential capabilities: ",
                "The GUI is most frequently used by casual or end users that are primarily",
                "An operating system can",
            ]
            tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            for i in range(0, 10):
                input_ids = tokenizer.encode(texts[i])
                output_ids = self.model_host.predict(input_ids)
                result = tokenizer.decode(output_ids)
                # print("Input: " + texts[i] + "------- Output: " + result)
                self.assertTrue(len(result) > 0)

        threads = [threading.Thread(target=send_requests) for i in range(0, 10)]
        [th.start() for th in threads]
        [th.join() for th in threads]


if __name__ == "__main__":
    unittest.main()
