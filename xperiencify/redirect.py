import os

import requests
import json
from flask.cli import load_dotenv
import random
import string

from xperiencify.exceptions import InvalidMagicLink


def create_student(api_key:str, email:str, firstname:str, lastname:str, course_id:str):
    """
    Create a new student in the Xperiencify platform.

    Parameters:
    - email (str): The email address of the student.
    - firstname (str): The first name of the student.
    - lastname (str): The last name of the student.

    Returns:
    - magic_link (str): The redirect link to take the student to their course.

    Example:
    >>> create_student('test@example.com', 'John', 'Doe')
    'https://www.xperiencify.io/course/123456'

    Note:
    - The API key must be set as an environment variable named XPERICIFY_API_KEY.
    - This method uses the Xperiencify API to create a new student.
    - If the password is not provided, a secure password will be generated and returned.
    """

    def generate_secure_password(length: int):
        """
        Generate a secure password of the given length.

        Parameters:
        - length (int): The length of the password to be generated.

        Returns:
        - secure_password (str): The randomly generated secure password.

        Example:
        >>> generate_secure_password(8)
        'X$6su9#8'

        Note: This method uses a combination of uppercase letters, lowercase letters, digits, and punctuation to
        generate a secure password.
        """
        characters = string.ascii_letters + string.digits + string.punctuation
        secure_password = ''.join(random.choice(characters) for i in range(length))
        return secure_password

    # make sure that the course id exists
    response = get_course_list(str(api_key))
    if response.status_code == 200:
        response = response.json()
        courses = {}
        for course in response:
            course_identifier = str(course['id'])
            course_title = str(course['title'])
            courses[course_identifier] = course_title

        if course_id not in courses.keys():
            course_ids = ", ".join(courses.keys())
            return "Course ID does not exist: " + course_id + ". Available course IDs: " + course_ids
    else:
        return "Error retrieving course list"

    api_url = "https://api.xperiencify.io/api/public/student/create/?api_key=" + str(api_key)
    data = {
        'student_email': email,
        'course_id': course_id,
        'first_name': firstname,
        'last_name': lastname,
        'password': generate_secure_password(8),
    }
    headers = {'Content-type': 'application/json'}
    response = requests.post(api_url, data=json.dumps(data), headers=headers)
    output = json.loads(response.text)
    magic_link = output['magic_link']  # this is the redirect link to take students to their course

    # make sure that the magic link is a proper link
    if magic_link.startswith("https:"):
        return magic_link
    else:
        raise InvalidMagicLink()


def get_course_list(key: str):
    #     $api_url = "https://api.xperiencify.io/api/public/coach/courses/?api_key={paste your key};   // Available from your Account page
    #
    #     $ch = curl_init();
    #     curl_setopt($ch, CURLOPT_URL, $api_url);
    #     curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "GET");
    #     $output = curl_exec($ch);

    # Example response:
    # [
    # 	{
    # 		"id": 199691,
    # 		"title": "Updates",
    # 		"slug": "program-updates",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/10-1592391603199.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2021-12-22T06:47:59.574913-08:00",
    # 		"users": [
    # 			238108
    # 		]
    # 	},
    # 	{
    # 		"id": 311962,
    # 		"title": "Kids - Basic Art Course 🎨",
    # 		"slug": "kids-basic-art-course",
    # 		"poster": "https://cdn-prod.xperiencify.com/users/16632/courses/311962/1654798789992.jpg",
    # 		"description": "<div>In this basic course, you will learn how to use a pencil, brush, color mixing, and draw 2 different drawings as an exercise.</div>",
    # 		"thumbnail": "",
    # 		"created": "2022-06-09T11:17:12.103147-07:00",
    # 		"users": [
    # 			782,
    # 			39872,
    # 			41061,
    # 			787304
    # 		]
    # 	},
    # 	{
    # 		"id": 589260,
    # 		"title": "Expiring Mini-Course Template",
    # 		"slug": "emc-template",
    # 		"poster": "https://cdn-prod.xperiencify.com/users/65735/courses/530157/1689354466900.jpg",
    # 		"description": "<div>Replace me with a description of your EMC</div>",
    # 		"thumbnail": "",
    # 		"created": "2023-06-15T08:41:31.853405-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 589265,
    # 		"title": "Copy of Expiring Mini-Course Template",
    # 		"slug": "emc-template-261095928441745",
    # 		"poster": "https://cdn-prod.xperiencify.com/users/65735/courses/530157/1689354466900.jpg",
    # 		"description": "<div>Replace me with a description of your EMC</div>",
    # 		"thumbnail": "",
    # 		"created": "2023-06-15T08:41:31.853405-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 475669,
    # 		"title": "Kids - Basic Art Course (Complete Access)",
    # 		"slug": "kids-basic-art-course-complete-access",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/5-1592391574093.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2023-04-03T02:45:58.349752-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 183742,
    # 		"title": "14 Day Challenge",
    # 		"slug": "14-day-challenge",
    # 		"poster": "https://cdn-prod.xperiencify.com/users/16632/courses/183742/1637554344892.png",
    # 		"description": "<div>This Is A <strong>14 Day CHALLENGE</strong> To Create Your Digital Business With The Right Steps. You'll Learn The Process That Elites Started With.</div>",
    # 		"thumbnail": "",
    # 		"created": "2021-11-21T20:06:18.608174-08:00",
    # 		"users": [
    # 			238108
    # 		]
    # 	},
    # 	{
    # 		"id": 475863,
    # 		"title": "14 Day Challenge (Elites)",
    # 		"slug": "14-day-challenge-elites",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/13-1592391616424.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2023-04-03T10:04:57.329568-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 32318,
    # 		"title": "WordPress™ Training",
    # 		"slug": "wp-training",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/8-1592391593609.jpeg",
    # 		"description": "<div>WordPress Training For WordPress Starters</div>",
    # 		"thumbnail": "",
    # 		"created": "2020-10-30T08:32:20.526119-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 477126,
    # 		"title": "WordPress™ Training (Complete Access)",
    # 		"slug": "wordpress-training-complete-access",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/5-1592391574093.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2023-04-05T05:58:38.743193-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 133536,
    # 		"title": "Online Business Basics 101 - Sep 2021 👈",
    # 		"slug": "online-business-basics-101-sep-2021",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/8-1592391593609.jpeg",
    # 		"description": "<div>IMPORTANT: Complete each training and do the action steps. Only click the completed button once you have \"REALLY\" done it. Don't cheat yourself. This training helps only if you follow through. Move quick but your own pace, we will be watching you, I mean seriously...'</div>",
    # 		"thumbnail": "",
    # 		"created": "2021-08-12T08:44:10.997987-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 107486,
    # 		"title": "Online Business Basics 101 Trial",
    # 		"slug": "obb-101-trial",
    # 		"poster": "https://cdn-prod.xperiencify.com/users/16632/courses/107486/1625753251596.gif",
    # 		"description": "<div>First-ever online business training for Maldivians to build your online business the right way.</div>",
    # 		"thumbnail": "",
    # 		"created": "2021-06-11T18:54:17.869932-07:00",
    # 		"users": [
    # 			39872
    # 		]
    # 	},
    # 	{
    # 		"id": 32117,
    # 		"title": "Online Business Basics 101",
    # 		"slug": "obb-101",
    # 		"poster": "https://cdn-prod.xperiencify.com/users/16632/courses/32117/1673900227729.jpg",
    # 		"description": "<div>First-ever online business training for Maldivians to build your online business the right way.</div>",
    # 		"thumbnail": "",
    # 		"created": "2020-10-29T21:12:59.681505-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 107380,
    # 		"title": "Phone Leads System Masterclass 🚀",
    # 		"slug": "phone-leads-system-masterclass",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/11-1592391607668.jpeg",
    # 		"description": "<div><strong><em>Phone Lead System Masterclass</em></strong> helps you utilize the YouTube™ search engine to get traffic to your video and get leads in an automated fashion.</div>",
    # 		"thumbnail": "",
    # 		"created": "2021-06-11T16:33:53.339625-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 32330,
    # 		"title": "Facebook™ Fundamentals",
    # 		"slug": "facebook-fundamentals",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/8-1592391593609.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2020-10-30T09:10:25.532314-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 32956,
    # 		"title": "Facebook™ Advanced",
    # 		"slug": "facebook-advanced",
    # 		"poster": "https://cdn-prod.xperiencify.com/users/16632/courses/32956/1604234676310.png",
    # 		"description": "<div>Facebook™ Advanced - Ads setup and creation for success.</div>",
    # 		"thumbnail": "",
    # 		"created": "2020-11-01T04:39:22.557287-08:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 107749,
    # 		"title": "Affiliate Marketing 101 👈",
    # 		"slug": "affiliate-marketing-101",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/2-1592391542782.jpeg",
    # 		"description": "<div><h2>🚀Affiliate Marketing Basics</h2></div><div><div>&nbsp;</div></div><div><div>This course briefly explain the process and fundamentals of affiliate marketing. Things to do and don'ts. This is a short, to the point like course, consists 5 module with short video lessons in each module.</div></div>",
    # 		"thumbnail": "",
    # 		"created": "2021-06-13T13:10:49.890802-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 116451,
    # 		"title": "Site Launch Design Checklist",
    # 		"slug": "site-launch-design-checklist",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/8-1592391593609.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2021-06-29T01:04:11.768592-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 131446,
    # 		"title": "Learn To Code With FLUTTER 👈",
    # 		"slug": "learn-to-code-with-flutter",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/6-1592391582160.jpeg",
    # 		"description": "<div>Learn To Code With FLUTTERLearn To Code With FLUTTER</div>",
    # 		"thumbnail": "",
    # 		"created": "2021-08-05T03:31:43.278885-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 135570,
    # 		"title": "Illustrator Fundamentals Course👈",
    # 		"slug": "illustrator-fundamentals-course",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/12-1592391611857.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2021-08-22T10:59:34.254466-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 161068,
    # 		"title": "Kids Collection Package",
    # 		"slug": "kids-collection-package",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/3-1592391556340.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2021-09-21T23:31:10.918926-07:00",
    # 		"users": [
    # 			39872
    # 		]
    # 	},
    # 	{
    # 		"id": 354076,
    # 		"title": "Awesome Course Name",
    # 		"slug": "awesome-course-1663337421175",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/1-1592391519821.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2022-09-16T07:10:21.736761-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 543024,
    # 		"title": "Awesome Course Name",
    # 		"slug": "awesome-course-1689001382986",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/8-1592391593609.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2023-07-10T08:04:58.538380-07:00",
    # 		"users": []
    # 	},
    # 	{
    # 		"id": 610770,
    # 		"title": "Awesome Course Name",
    # 		"slug": "awesome-course-1697727429345",
    # 		"poster": "https://cdn-prod.xperiencify.com/coreImages/1-1592391519821.jpeg",
    # 		"description": "",
    # 		"thumbnail": "",
    # 		"created": "2023-10-19T07:59:46.024657-07:00",
    # 		"users": []
    # 	}
    # ]

    api_url = "https://api.xperiencify.io/api/public/coach/courses/?api_key=" + str(key)
    return requests.get(api_url)


if __name__ == "__main__":
    email = "example@example.com"
    firstname = "John"
    lastname = "Doe"
    magic_link = create_student(email, firstname, lastname)
    print(magic_link)
