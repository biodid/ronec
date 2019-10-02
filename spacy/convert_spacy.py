"""

This script converts the RONEC(Romanian Named Entity Corpus) to three files(train, dev, eval) in json format that are
necessary to train and evaluate models with the Spacy command line interface.

More information can be found at: https://spacy.io/api/cli#convert

"""


import argparse
import subprocess
import os
import re
import sys
import ntpath


ent_dict = {
    "-TETIME": "-DATETIME",
    "-MERIC_VALUE": "-NUMERIC_VALUE",
    "-RSON": "-PERSON",
    "-GANIZATION": "-ORGANIZATION",
    "-T_REL_POL": "-NAT_REL_POL",
    "-E\"": "-GPE\"",
    "-C\"": "-LOC\"",
    "-CILITY": "-FACILITY",
    "-ODUCT": "-PRODUCT",
    "-ENT": "-EVENT",
    "-NGUAGE": "-LANGUAGE",
    "-RK_OF_ART": "-WORK_OF_ART",
    "-RIOD": "-PERIOD",
    "-NEY": "-MONEY",
    "-ANTITY": "-QUANTITY",
    "-DINAL": "-ORDINAL"
}


def create_file_json_collubio(sentences, output_path, output_filename):
    """
        This function creates a json file that contains CoNLL-U BIO information about RONEC.

        Args:
            sentences (list): list containing the train, dev or eval sentences.
            output_directory (str): the output directory of the resulted files.
            output_filename (str): the output file name: train_ronec.json, dev_ronec.json or eval_ronec.json.
    """

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # write all the selected sentences to a temporary file in CoNLL-U BIO format
    with open(output_filename, "w", encoding="utf-8") as file:
        for sentence in sentences:
            for tokens_list in sentence:
                if type(tokens_list) == str:
                    file.write(tokens_list)
                else:
                    file.write("\t".join(tokens_list) + "\n")

            file.write("\n")

    # convert the CoNLL-U BIO temporary file file to Spacy json CoNLL-U BIO
    _ = subprocess.run("python -m spacy convert {} {} --converter conllubio".
                       format(output_filename, output_path))

    with open(os.path.join(output_path, ntpath.basename(output_filename)), "r", encoding="utf-8") as file:
        text = file.read()

        for wrong_ent, correct_ent in ent_dict.items():
            text = re.sub(wrong_ent, correct_ent, text)

    with open(os.path.join(output_path, ntpath.basename(output_filename)), "w") as file:
        file.write(text)

    # clean up
    os.remove(output_filename)


def extract_sentences_from_file(ronec_path):
    """
        This function extracts the sentences with the tokens from the RONEC and puts them in a list.

        Args:
            ronec_path (str): path to RONEC

        Returns:
            A list that contains the sentences of the RONEC.
    """
    sentences = []

    # creating a temp file that can be read by spacy convertor
    with open(ronec_path, "r", encoding="utf-8") as file:

        old_entity = None

        tokens_list = None

        for line in file:
            # if the current line denotes a beginning of a new sentence, create a new list that will contain the tokens
            if line[0] == "#":
                tokens_list = []
                tokens_list.append(line)
                tokens_list.append(file.readline())
            # if the current line denotes the end of the sentences, add the list of tokens to the sentence list
            elif line == "\n":
                sentences.append(tokens_list)
            # else process the tokens and add them to the token list
            else:
                tokens = line.split()

                # remove the second last token to obtain the correct number of tokens for Spacy
                del tokens[-2]

                # convert the entities to BIO format
                entity = tokens[-1]

                if entity == "*":
                    tokens[-1] = "O"

                elif entity.__contains__(":"):
                    old_entity = entity.split(":")[-1]
                    tokens[-1] = "I" + old_entity[1:]
                else:
                    tokens[-1] = "I" + old_entity[1:]

                tokens_list.append(tokens)

    return sentences


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("ronec_path", type=str)
    parser.add_argument("output_path", type=str)
    parser.add_argument("--dev_ratio", type=float, default=0.1)

    args = parser.parse_args()

    ronec_path = args.ronec_path
    output_path = args.output_path
    dev_ratio = args.dev_ratio

    if dev_ratio < 0 or dev_ratio > 1:
        raise argparse.ArgumentTypeError("Argument validation_ratio must be a float between 0 and 1.")

    # extract the sentences from RONEC
    sentences = extract_sentences_from_file(ronec_path)

    # create the train, dev and eval sentences
    num_sentences = 5127  # source: https://github.com/dumitrescustefan/ronec
    num_train_sentences = int((1 - dev_ratio) * num_sentences)
    num_dev_sentences = num_sentences - num_train_sentences

    train_sentences = sentences[0: num_train_sentences]
    dev_sentences = sentences[num_train_sentences: num_train_sentences + num_dev_sentences]

    # create the train, dev and eval json files necessary for Spacy
    print("Running convert conllup to spacy json script...\n")
    print("Total sentences: {}...".format(num_sentences))
    print("Validation ratio is {}, resulting in {} train sentences and {} dev sentences...\n".
          format(dev_ratio, num_train_sentences, num_dev_sentences))

    create_file_json_collubio(train_sentences,
                              output_path, os.path.join(os.path.dirname(sys.argv[0]), "train_ronec.json"))

    create_file_json_collubio(dev_sentences,
                              output_path, os.path.join(os.path.dirname(sys.argv[0]), "dev_ronec.json"))



