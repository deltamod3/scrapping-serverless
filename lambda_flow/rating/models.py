import boto3

# Table Names
tbl_tmp_searches = 'tmp_searches'
tbl_tmp_results_step1 = 'tmp_results_step1'
tbl_tmp_results_step2 = 'tmp_results_step2'
tbl_tmp_results_step3 = 'tmp_results_step3'

# fields of tmp_searches table
tmp_searches_search_id = 'search_id' # N
tmp_searches_keyword = 'keyword' # N
tmp_searches_description = 'description' # S
tmp_searches_technology = 'technology' # S
tmp_searches_created_at = 'created_at' # N
tmp_searches_updated_at = 'updated_at' # N
tmp_searches_total_crawled_result = 'total_crawled_result' # N
tmp_searches_purpose = 'purpose' # S
tmp_searches_user_id = 'user_id' # S
tmp_searches_search_engine = 'search_engine'  # S

# fields of tmp_results table
tmp_results_result_id = 'result_id' # N, all steps
tmp_results_search_id = 'search_id' # N, all steps
tmp_results_url = 'url' # S, step1
tmp_results_title = 'title' # S, step1
tmp_results_description = 'description' # S, step1
tmp_results_category_id = 'category_id' # N, TODO Not used for now
tmp_results_matched_similarity = 'matched_similarity' # N, step3
tmp_results_date = 'date' # N, all steps
tmp_results_type = 'type' # N, step2
tmp_results_image_url = 'image_url' # S, TODO Not used for now
tmp_results_text = 'text' # S, step2


def get_dynamodb_table(table_name, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
    return dynamodb.Table(table_name)
