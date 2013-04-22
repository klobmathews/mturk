# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from boto.mturk.question import (
    AnswerSpecification,
    FormattedContent,
    FreeTextAnswer,
    Overview,
    Question,
    QuestionContent,
    QuestionForm,
    SelectionAnswer,
)

from boto.mturk.connection import MTurkConnection

# <markdowncell>

# __Create a Mechanical Turk Connection using your AWS credentials__

# <codecell>

import pickle
f = open('/Users/kellyo/mech_turk/creds.pk', 'rb')
creds = pickle.load(f)
f.close()

# <codecell>

mtc = MTurkConnection(
    aws_access_key_id=creds['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=creds['AWS_SECRET_ACCESS_KEY'],
    host=creds['HOST'],
)
mtc

# <markdowncell>

# __Testing: Retrieve the account balance__

# <codecell>

print mtc.get_account_balance()

# <markdowncell>

# __Data to do stuff with__

# <codecell>

from IPython.display import Image
from IPython.core.display import display

# <codecell>

urls = [
    'http://media.egotvonline.com/wp-content/uploads/2011/10/costume-dogs-in-fast-food-costumes.jpg?41ed4f',
    'http://runt-of-the-web.com/wordpress/wp-content/uploads/2012/10/awkward-halloween-dad.jpg',
]
shuffle(urls)
selections = (('Person', 0), ('Animal', 1), ('WTF', 2))

# <codecell>

for url in urls:
    img = Image(url=url)
    display(img)

# <codecell>

description = 'Look at images and determine if the photo is of a person or a pet.'
title = 'Determine if the photo is a person or a pet.'
keywords = ['pets', 'people', 'photos', 'classification']

# <markdowncell>

# __Retrieve previously posted HITs and disable them.__

# <codecell>

def remove_all_hits(mtc): 
    all_hits = mtc.get_all_hits() 
    for hit in all_hits: 
        mtc.disable_hit(hit.HITId) 
        print 'Disabled: ', hit.HITId 

# <codecell>

remove_all_hits(mtc)

# <headingcell level=3>

# Construct a HIT

# <markdowncell>

# __Using a Question Form__

# <codecell>

def add_image(url, overview, _id, width=20, height=20):
    """Add an image to :param overview:. """
    overview.append_field('Text', title)
    overview.append(FormattedContent(
        '<img src="{0}" alt="doc{1}" height="500" width="500"></img>'.format(url, _id)))
    return overview

# <codecell>

def make_mc_question(url, selections, _id=''):
    """Create a multiple choice question to classify :param urls:."""
    content = QuestionContent()
    content = add_image(url, content, _id)
    content.append_field(
        'Title', description)
    answers = SelectionAnswer(
        max=1,
        min=1,
        other=False,
        selections=selections,
        style='radiobutton',
        type='text',
    )
    question = Question(
        answer_spec=AnswerSpecification(answers),
        content=content,
        identifier='{0}'.format(url),
        is_required=True,
    )
    return question

# <codecell>

mc_question = make_mc_question(urls[0], selections, _id='')

# <codecell>

def make_question(url, selections):
    """Build a formatted question to be posted on mechanical turk.

    :param urls: Images to be displayed in mc question.
    :param selections: Answer selections.
    :param fta: True if the question includes a FreeTextAnswer.

    """
    mc_overview = Overview()
    mc_overview.append_field('Title', title)

    question_form = QuestionForm()
    question_form.append(mc_overview)
    question_form.append(make_mc_question(url, selections))
    return question_form

# <codecell>

question = make_question(urls[0], selections)

# <headingcell level=3>

# Set Qualifications and Requirements

# <codecell>

from boto.mturk.qualification import (
    Requirement,
    Qualifications,
)

# <markdowncell>

# __Create Custom Qulaification ID__

# <markdowncell>

# __You'll need test data for your qualification test__

# <codecell>

test_url = 'http://julien.danjou.info/media/images/lolcat-testing.jpg'
test_answer = dict(selections)['Animal']

# <codecell>

img = Image(url=test_url); img 

# <codecell>

def create_answer_xml(indentifier, selection, score):
    xml_string = (
        '<Question>'
        '<QuestionIdentifier>{0}</QuestionIdentifier>'
        '<AnswerOption>'
        '<SelectionIdentifier>{1}</SelectionIdentifier>'
        '<AnswerScore>{2}</AnswerScore>'
        '</AnswerOption>'
        '</Question>'
    ).format(indentifier, selection, score)
    return xml_string

# <codecell>

test_question = make_question(test_url, selections)

# <codecell>

answer_key = "<AnswerKey xmlns='{0}'>".format('http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/AnswerKey.xsd')
answer_key += create_answer_xml(test_url, test_answer, 1)
answer_key += '</AnswerKey>'

# <codecell>

answer_key

# <codecell>

def create_custom_qual_id(test_question, answer_key):
    quals = mtc.create_qualification_type(
        answer_key=answer_key,
        auto_granted=False,
        description=description,
        keywords=keywords,
        name='My Unique Name',
        retry_delay=None,
        status='Active',
        test=test_question,
        test_duration=3600,
    )
    qual = quals.pop()
    print qual.Name
    print qual.QualificationTypeId
    return qual.QualificationTypeId

# <codecell>

# custom_id = create_custom_qual_id(test_question, answer_key)

# <codecell>

# mtc.dispose_qualification_type('2ZS6KW4ZMAZHU4P2P8ROQNVRH418HM')

# <markdowncell>

# _custom_id_: 2ZS6KW4ZMAZHU4P2P8ROQNVRH418HM

# <codecell>

custom_qualification_id = '2ZS6KW4ZMAZHU4P2P8ROQNVRH418HM'

# <codecell>

def make_qual_type(
    comparator="Exists",
    integer_value=None,
    qual_type=custom_qualification_id,
    required_to_preview=False,
):
    """Creates a qualification requirement for workers to accept HITs."""
    return Requirement(
        comparator=comparator,
        integer_value=integer_value,
        qualification_type_id=qual_type,
        required_to_preview=required_to_preview,
)

# <codecell>

custom_qual_type = make_qual_type(
    comparator="GreaterThanOrEqualTo",
    integer_value=1,
    qual_type=custom_qualification_id,
    required_to_preview=False,
)

# <codecell>

qualifications = Qualifications()
qualifications.add(custom_qual_type)

# <codecell>

from collections import defaultdict

ONE_HOUR = 3600  # seconds
ONE_DAY = ONE_HOUR * 24
ONE_WEEK = ONE_HOUR * 24 * 7

# <codecell>

hits = defaultdict(lambda : defaultdict())

# <codecell>

for url in urls:
    hit = mtc.create_hit(
        annotation=None,
        approval_delay=1,
#       approval_delay=ONE_DAY,
        description=description,
        duration=ONE_HOUR,
        keywords=keywords,
        lifetime=ONE_WEEK,
        max_assignments=1,
        qualifications=qualifications,
        questions=make_question(url, selections),
        response_groups=[
            'HITAssignmentSummary', 'HITDetail', 'HITQuestion', 'Minimal'],
        reward=0.02,
        title=title,
    )
    hits[hit[0].HITId] = {'url': url}

# <codecell>

print 'Created Hits: '
for hit in hits.keys():
    print hit

# <headingcell level=4>

# Turkers will preview, accept and respond to HITS.

# <headingcell level=3>

# Retrieve and review thier response:

# <codecell>

def get_reviewable_hits(page_num=1, page_size=10):
    """Return all hits on the :param page_num:, with :param page_size:."""
    return mtc.get_reviewable_hits(
        page_number=page_num,
        page_size=page_size,
        sort_by='Enumeration'
    )

# <codecell>

reviewable_hits = get_reviewable_hits()

# <codecell>

def parse_assignments(assignments):
        """Extract each answer from ::param assignments::."""
        for assignment in assignments:
            classification = _parse_answers(assignment)
        return classification

# <codecell>

def _parse_answers(assignment):  # pragma no cover
    """Return a list of dicts, each containing an answer's details."""
    classification = {}
    answer = assignment.answers[0][0]
    if not answer.fields[0]:
        return
    ind_id = int(answer.fields[0])
    classification.update({'selection': selections[ind_id][0]})
    classification.update({'selection_id': ind_id})
    classification.update({'worker_id': assignment.WorkerId})
    return classification

# <codecell>

for hit in reviewable_hits:
    assignments = mtc.get_assignments(hit.HITId)
    responses = parse_assignments(assignments)
    hits[hit.HITId].update(responses)
    print hits[hit.HITId].get('selection')
    img = Image(url=hits[hit.HITId]['url'])
    display(img)

# <codecell>

for hit, values in hits.iteritems():
    print 'HitId: {0}, Selection: {1}, Selection Id: {2}'.format(hit, values.get('selection'), values.get('selection_id'))
    

# <codecell>

import pandas
pandas.DataFrame(hits)

