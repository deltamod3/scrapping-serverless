import json
import operator
import nltk
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from response_lib.helper import bad_request_error, api_response, internal_server_error

nltk.data.path.append("/tmp")
nltk.download("punkt", download_dir="/tmp")
nltk.download("stopwords", download_dir="/tmp")
nltk.download("wordnet", download_dir="/tmp")


def handler(event, context):
    print(event)
    event_body = event.get('body', None)
    if not event_body:
        return bad_request_error("Missing body")
    request_body = json.loads(event_body)
    technologies = request_body.get('technologies', None)
    text = request_body.get('text', None)
    if not technologies or not text:
        return bad_request_error("Invalid body")
    try:
        different_text = []
        print(text)
        for tech in technologies:
            keywords = find_similarity_keyword(tech, text)
            ref_key = keywords["list_ref_key"]
            if ref_key["total_count"] != 0:
                texts = {tech: text}
                different_text.append(texts)
        print(different_text)
        return api_response(different_text)
    except Exception as e:
        return internal_server_error(e)


def find_similarity_keyword(text, text2):
    wnl = WordNetLemmatizer()
    """For total Words of Test2"""
    split_list_text1 = text.split()
    split_list_text2 = text2.split()

    """Tokenize Both the text"""
    text1_tokens = word_tokenize(text.lower())
    text2_tokens = word_tokenize(text2.lower())

    """Creating The Word List and removing stopwords(a, an ,the) Of all Tokenize text"""
    tokens_without_sw_text1 = [word for word in text1_tokens if not word in stopwords.words()]
    tokens_without_sw_text2 = [word for word in text2_tokens if not word in stopwords.words()]

    """Removing plural from both the text and overriding the value"""
    tokens_without_sw_text1 = [wnl.lemmatize(i) for i in tokens_without_sw_text1]
    tokens_without_sw_text2 = [wnl.lemmatize(i) for i in tokens_without_sw_text2]

    """Removing unnecessary single line keywords"""
    tokens_without_sw_text1 = [i for i in tokens_without_sw_text1 if len(i) > 1]
    tokens_without_sw_text2 = [i for i in tokens_without_sw_text2 if len(i) > 1]
    """Removing declension(ed) from the text1 and overriding the value"""
    for text1_words in tokens_without_sw_text1:
        for suffix in ['ed']:
            if text1_words.endswith(suffix):
                """Taking index value of "ed" word"""
                index = tokens_without_sw_text1.index(text1_words)
                """Pop that word from list"""
                tokens_without_sw_text1.pop(index)
                """Removing "ed" from the word and append into list"""
                result = text1_words[:-len(
                    suffix)]
                tokens_without_sw_text1.append(result)

    """Removing declension(ed) from the text1 and overriding the value"""
    for text2_words in tokens_without_sw_text2:
        for suffix in ['ed']:
            if text2_words.endswith(suffix):
                """Taking index value of "ed" word"""
                index = tokens_without_sw_text2.index(text2_words)
                """Pop that word from list"""
                tokens_without_sw_text2.pop(index)
                """Removing "ed" from the word and append into list"""
                result = text2_words[:-len(suffix)]
                tokens_without_sw_text2.append(result)

    """Removing wanted special_keywords(@#$%>,)"""
    alphanumeric_for_text2 = [character for character in tokens_without_sw_text2 if
                              character.isalnum() or character.isspace() or character.isalpha()]
    alphanumeric_for_text1 = [character for character in tokens_without_sw_text1 if
                              character.isalnum() or character.isspace() or character.isalpha()]

    """Creating "set" of both the keyword list"""
    setA = set(alphanumeric_for_text1)
    setB = set(alphanumeric_for_text2)

    """Separating the similar and non similar words From both the list of text"""
    overlap = setA & setB
    universe = setA | setB
    """Calculating the repeated words in list of text1"""
    counts_for_text1 = Counter(alphanumeric_for_text1)
    """Creating set For list of text1(FOR_: tot_unique_k)"""
    set_counter_text1 = set(counts_for_text1)

    """Counting repeated words(FOR_: tot_k_rep)"""
    count_rep_keyword_text1 = 0
    for key, count in counts_for_text1.items():
        count_rep_keyword_text1 += count

    """Calculating the repeated words in list of text2"""
    counts_for_text2 = Counter(alphanumeric_for_text2)
    set_counter = set(counts_for_text2)
    """Separating similar key_words from both the list of text"""
    similar_words = set_counter_text1 & set_counter
    tot_key_rep_text2 = 0
    tot_rep_key = 0
    """Count total repeated key_word from text1 to text2(FOR_: tot_ref_k) and total key_words(FOR_: repetition)"""
    for key, count in counts_for_text2.items():
        tot_key_rep_text2 += count
        if key in counts_for_text1:
            tot_rep_key += count  # + counts_for_text1[key]
    """Adding Total number of keywords and list of keywords"""
    unique_key_text1 = len(counts_for_text1)
    unique_key_text2 = len(counts_for_text2)
    list_keyword_text1 = counts_for_text1
    list_keyword_text2 = counts_for_text2

    """Adding Total number of keywords_repeated"""
    tot_key_rep_text1 = count_rep_keyword_text1
    tot_key_rep_text2 = tot_key_rep_text2

    """Adding Total number of keywords are present in text2 and list of those keywords"""
    tot_ref_key = len(overlap)
    list_ref_key = {}
    total_list_ref_count = 0
    for value in overlap:
        total_count = counts_for_text1[value] + counts_for_text2[value]
        list_ref_key[value] = total_count
        total_list_ref_count += total_count
    list_ref_key['total_count'] = total_list_ref_count

    """Set dictionary To descending order"""
    list_ref_key = dict(sorted(list_ref_key.items(), key=operator.itemgetter(1), reverse=True))
    list_keyword_text1 = dict(sorted(list_keyword_text1.items(), key=operator.itemgetter(1), reverse=True))
    list_keyword_text2 = dict(sorted(list_keyword_text2.items(), key=operator.itemgetter(1), reverse=True))

    """Calculating Percentage For both the list of Text"""
    result = float(len(overlap)) / len(universe) * 100
    data = {'percentage': result,
            'unique_key_text1': unique_key_text1,
            'unique_key_text2': unique_key_text2,
            'list_keyword_text1': list_keyword_text1,
            'list_keyword_text2': list_keyword_text2,
            'tot_key_rep_text1': tot_key_rep_text1,
            'tot_key_rep_text2': tot_key_rep_text2,
            'tot_ref_key': tot_ref_key,
            'list_ref_key': list_ref_key,
            'tot_rep_key': tot_rep_key,
            'total_word_text1': len(split_list_text1),
            'total_word_text2': len(split_list_text2)
            }
    return data
