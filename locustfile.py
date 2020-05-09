from locust import HttpLocust, TaskSet
from locust.contrib.fasthttp import FastHttpLocust
import json
from faker import Factory

languages_endpoint = "/api/v2.3/exams/load-testing/languages/"  # Exam slug needs to changed accordingly
exam_endpoint = "/api/v2.2/exams/load-testing/attempts/"  # Exam slug needs to changed accordingly
questions_endpoint = "/api/v2.2/attempts/{}/questions/"
usa_endpoint = "/api/v2.2/attempts/{}/questions/{}/"

# Json need to be changed according to exam
exam_data = {
    "exam": {
        "url": "https://demo.testpress.in/api/v2.2/exams/load-testing/",
        "id": 795,
        "title": "load-testing",
        "description": "",
        "start_date": "2019-09-18T22:08:51+05:30",
        "end_date": None,
        "duration": "3:00:00",
        "number_of_questions": 169,
        "negative_marks": "0.00",
        "mark_per_question": "1.00",
        "template_type": 2,
        "allow_retake": True,
        "max_retakes": -1,
        "enable_ranks": False,
        "rank_publishing_date": None,
        "attempts_url": "https://demo.testpress.in/api/v2.2/exams/load-testing/attempts/",
        "attempts_count": 0,
        "paused_attempts_count": 0,
        "allow_pdf": False,
        "allow_question_pdf": False,
        "created": "2019-09-18T16:39:14.788376Z",
        "slug": "load-testing",
        "variable_mark_per_question": False,
        "show_answers": True,
        "comments_count": 0,
        "allow_preemptive_section_ending": False,
        "sections": [{"order": 0, "name": "", "duration": "3:00:00", "cut_off": 0}],
        "immediate_feedback": False,
        "categories": [],
        "toppers": [],
        "device_access_control": "both",
        "instructions": "",
        "show_percentile": True,
        "show_score": True,
        "languages": [],
        "students_attempted_count": 0,
        "custom_end_message": "",
        "custom_redirect_url": "",
    },
    "user": {
        "id": 5930,  # Need to be changed
        "batches": [],
        "url": "https://demo.testpress.in/api/v2.1/users/5930/",  # Need to be changed
        "username": "test1",
        "display_name": "test1",
        "first_name": "test1",
        "last_name": "",
        "email": "",
        "photo": "",
        "large_image": "https://media.testpress.in/static/img/default_large_image.png",
        "medium_image": "https://media.testpress.in/static/img/default_medium_image.png",
        "small_image": "https://media.testpress.in/static/img/default_small_image.png",
        "x_small_image": "https://media.testpress.in/static/img/default_x_small_image.png",
        "mini_image": "https://media.testpress.in/static/img/default_mini_image.png",
        "birth_date": None,
        "gender": None,
        "address1": "",
        "address2": "",
        "city": "",
        "zip": "",
        "state": "",
        "phone": "",
    },
}


def login(l):
    # r = l.client.get("/login/")
    # csrftoken = r.cookies['csrftoken']
    # r = l.client.post("/login/", {"username": "test1", "password": "test", "csrfmiddlewaretoken": csrftoken}, headers={'X-CSRFToken': csrftoken, 'Referer': l.parent.host + '/login/'})
    l.csrftoken = "csrftoken"


def logout(l):
    l.client.get("/logout")

def start_exam(l):
    fake = Factory.create()
    l.client.get(languages_endpoint)
    exam_data["phone"] = fake.phone_number()
    exam_data["name"] = fake.first_name()
    exam_data["email"] = fake.email()
    r = l.client.post(
        exam_endpoint,
        exam_data,
        headers={
            "X-CSRFToken": l.csrftoken,
            "Referer": l.parent.host + "/login/",
            "cookie": json.dumps(l.locust.client.cookiejar._cookies),
        },
    )
    l.attempt_id = r.json().get("id")
    r = l.client.get(
        questions_endpoint.format(l.attempt_id) + "?bonus=False&page=1",
        headers={"X-CSRFToken": l.csrftoken, "Referer": l.parent.host + "/login/"},
    )
    total_page = r.json().get("count") // r.json().get("per_page")
    usas = r.json().get("results")
    if r.json().get("count") % r.json().get("per_page"):
        total_page += 1
    for page in range(total_page):
        if page not in [0, 1]:
            r = l.client.get(
                questions_endpoint.format(l.attempt_id) + "?bonus=False&page={}".format(page),
                headers={"X-CSRFToken": l.csrftoken, "Referer": l.parent.host + "/login/"},
            )
            usas.extend(r.json().get("results"))
    usa_dict = {}
    for usa in usas:
        usa_dict[usa["id"]] = usa
    l.usa_dict = usa_dict


def take_exam(l):
    for usa_id, usa_data in getattr(l.usa_dict, "iteritems", l.usa_dict.items)():
        l.client.put(usa_endpoint.format(l.attempt_id, usa_id), data=json.dumps(usa_data), headers={"Content-Type": "application/json"})


class UserBehavior(TaskSet):
    tasks = {take_exam: 200}
    csrftoken = ""
    attempt_id = 0
    usa_dict = {}

    def on_start(self):
        login(self)
        # index(self)
        start_exam(self)

    def on_stop(self):
        logout(self)


class WebsiteUser(FastHttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 10000
