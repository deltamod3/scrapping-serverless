import json
import math
import re
import nltk
from nltk import WordNetLemmatizer as wnl
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from multiprocessing import Process, Pipe
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
    extracted_text = request_body.get('text', None)
    purpose = request_body.get('purpose', None)
    reference_text = request_body.get('reference_text', None)
    if not extracted_text:
        return bad_request_error("Invalid extracted_text")
    if not reference_text:
        return bad_request_error("Invalid reference_text")
    try:
        extracted_text = extracted_text.lower()
        reference_text = reference_text.lower()
        ratings = replica_find_rating_percentage(extracted_text, reference_text)
        word_result = extracted_text
        if purpose:
            purpose = purpose.lower()
            word_result = replica_similarity_keyword(purpose, extracted_text)
        words = list(word_result)
        lines = find_uniquePhrases(words, extracted_text)
        percentage = 0
        if purpose:
            test = replica_cosine_similarity(purpose, lines)
            percentage = test['percentage']
        purp = ratings + percentage
        new_rating = round(purp)
        rat = {"rating": ratings, "new_rating": new_rating, "purpose": percentage}
        print(rat)
        return api_response(dict(Result=rat))
    except Exception as e:
        return internal_server_error(e)


def find_keyword_repetition(text, text2, conn):
    """Tokenize Both the text"""
    text1_tokens = word_tokenize(text)
    text2_tokens = word_tokenize(text2)

    """Creating The Word List and removing stopwords(a, an ,the) Of all Tokenize text"""
    tokens_without_sw_text1 = [word for word in text1_tokens if not word in stopwords.words()]
    tokens_without_sw_text2 = [word for word in text2_tokens if not word in stopwords.words()]

    """Removing plural from both the text and overriding the value"""
    tokens_without_sw_text1 = [wnl().lemmatize(i) for i in tokens_without_sw_text1]
    tokens_without_sw_text2 = [wnl().lemmatize(i) for i in tokens_without_sw_text2]
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
                result = text1_words[:-len(suffix)]
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
    alphanumeric_for_text1 = [character for character in tokens_without_sw_text1 if
                              character.isalnum() or character.isspace() or character.isalpha()]
    alphanumeric_for_text2 = [character for character in tokens_without_sw_text2 if
                              character.isalnum() or character.isspace() or character.isalpha()]

    """Calculating the repeated words in list of text1"""
    counts_for_text1 = Counter(alphanumeric_for_text1)

    """Calculating the repeated words in list of text2"""
    counts_for_text2 = Counter(alphanumeric_for_text2)

    tot_key_rep_text2 = 0
    tot_rep_key = 0
    """Count total repeated key_word from text1 to text2(FOR_: tot_ref_k) and total key_words(FOR_: repetition)"""
    for key, count in counts_for_text2.items():
        tot_key_rep_text2 += count
        if key in counts_for_text1:
            tot_rep_key += count  # + counts_for_text1[key]

    """Adding Total number of keywords_repeated"""
    tot_key_rep_text2 = tot_key_rep_text2

    """Calculating Percentage For both the list of Text"""
    result = tot_rep_key / tot_key_rep_text2 * 100

    data = {'percentage': result}
    conn.send(data)
    conn.close()


def text_to_cosine(text):
    search = str(text)
    WORD = re.compile(r'\w+')
    words = WORD.findall(search)
    return Counter(words)


def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
    sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


def find_cosine_similarity(text1, text2, conn):
    vector1 = text_to_cosine(text1)
    vector2 = text_to_cosine(text2)
    cosine = get_cosine(vector1, vector2)
    print(cosine)
    Cosine_value = cosine * 100
    print(Cosine_value)
    conn.send(Cosine_value)
    conn.close()


def find_rating(cosine_value, keyword_repetition_value):
    if len(cosine_value) != len(keyword_repetition_value):
        return {"Error": 'Value is missing'}
    rating_result = []
    for index_value in range(len(cosine_value)):
        calculating_formula = cosine_value[index_value] * 75 + keyword_repetition_value[index_value] * 25
        calculating_parentage = calculating_formula / 100
        if keyword_repetition_value[index_value] >= 100:
            calculating_parentage = calculating_parentage + calculating_parentage * 25 / 100
        if calculating_parentage >= 100:
            calculating_parentage = 100
        rating_result.append({'rating_' + str(index_value): calculating_parentage})
    return {"Total_Rating": rating_result}


def find_cosine_similarity_with_keyword_repetition(text, text2):
    """Find Rating value"""

    # create a list to keep all processes
    processes = []

    # create a list to keep connections
    parent_connections = []

    # create a process per instance
    for x in [0, 1]:
        # create a pipe for communication
        parent_conn, child_conn = Pipe()
        parent_connections.append(parent_conn)
        if x == 0:
            # create the process, pass instance and connection
            process = Process(target=find_cosine_similarity, args=(text, text2, child_conn))
        else:
            process = Process(target=find_keyword_repetition, args=(text, text2, child_conn))
        processes.append(process)

    # start all processes
    for process in processes:
        process.start()

    # make sure that all processes have finished
    for process in processes:
        process.join()

    """Take Result From cosine and keyword repetition"""
    cosine_value = parent_connections[0].recv()
    print(cosine_value)
    keyword_repetition_value = parent_connections[1].recv()
    print(keyword_repetition_value)
    """Find Rating value"""
    total_percentage = find_rating([cosine_value], [keyword_repetition_value['percentage']])
    print(total_percentage)
    return {'total_percentage': total_percentage['Total_Rating'][0]['rating_0'],
            'cosine_value': int(cosine_value),
            'keyword_repetition_value': int(keyword_repetition_value['percentage'])}
    # with concurrent.futures.ProcessPoolExecutor() as executor:
    #     """Find cosine_similarity and keyword repetition value parallel"""
    #     cosine_value = executor.submit(find_cosine_similarity, text, text2)
    #     keyword_repetition_value = executor.submit(find_keyword_repetition, text, text2)
    #     """Take Result From cosine and keyword repetition"""
    #     cosine_value = cosine_value.result()
    #     print(cosine_value)
    #     keyword_repetition_value = keyword_repetition_value.result()
    #     print(keyword_repetition_value)
    #     """Find Rating value"""
    #     total_percentage = find_rating([cosine_value], [keyword_repetition_value['percentage']])
    #     print(total_percentage)
    #     return {'total_percentage': total_percentage['Total_Rating'][0]['rating_0'],
    #             'cosine_value': int(cosine_value),
    #             'keyword_repetition_value': int(keyword_repetition_value['percentage'])}


def replica_similarity_keyword(text, text2):
    """For total Words of Test2"""
    # split_list_text1 = text.split()
    # split_list_text2 = text2.split()

    """Tokenize Both the text"""
    text1_tokens = word_tokenize(text)
    text2_tokens = word_tokenize(text2)

    """Creating The Word List and removing stopwords(a, an ,the) Of all Tokenize text"""
    tokens_without_sw_text1 = [word for word in text1_tokens if not word in stopwords.words()]
    tokens_without_sw_text2 = [word for word in text2_tokens if not word in stopwords.words()]

    """Removing plural from both the text and overriding the value"""
    tokens_without_sw_text1 = [wnl().lemmatize(i) for i in tokens_without_sw_text1]
    tokens_without_sw_text2 = [wnl().lemmatize(i) for i in tokens_without_sw_text2]

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
    print(set_counter_text1)
    tot_ref_key = len(overlap)
    print(tot_ref_key)
    return set_counter_text1


def find_uniquePhrases(words, text2):
    sentences = text2.split('.')
    lines = []
    for sentence in sentences:
        for word in words:
            if word in sentence:
                line = sentence
                lines.append(line)

    return lines


def replica_cosine_similarity(text1, text2):
    val = []
    new_lines = []
    phrases = []
    for line in text2:
        line = line.strip()
        if line not in new_lines:
            new_lines.append(line)
    lines = list(set(text2))
    for line in new_lines:
        vector1 = text_to_cosine(text1)
        vector2 = text_to_cosine(line)
        cosine = get_cosine(vector1, vector2)
        Cosine_value = cosine * 100
        if Cosine_value != 0.0:
            value = {Cosine_value}
            linecoisne = {line: value}
            phrases.append(linecoisne)
            val.append(value)
    number = len(val)
    percentage = []
    for vals in val:
        word_val = sum(vals)
        percentage.append(word_val)
    results = 0
    if number != 0:
        results = sum(percentage) / number
    data = {"percentage": results, "phrases": phrases}
    return data


def replica_find_rating_percentage(extracted_text, reference_text):
    similarity_dict = find_cosine_similarity_with_keyword_repetition(reference_text, str(extracted_text))
    similarity = similarity_dict['total_percentage']
    return similarity
