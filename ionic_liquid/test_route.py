import os
views_path = os.path.dirname(os.path.abspath('ionic_liquid/views.py'))
test_box_path = os.path.join(views_path, 'ionic_liquid', 'test_box', 'query_similar_IL')
print('Views path:', views_path)
print('Test box path:', test_box_path)
print('Test box exists:', os.path.exists(test_box_path))
print('Files:', os.listdir(test_box_path) if os.path.exists(test_box_path) else 'N/A')