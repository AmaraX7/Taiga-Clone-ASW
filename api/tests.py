import json

from django.contrib.auth.models import User
from django.test import TestCase

from issues.models import Comment, Issue, IssueActivity, IssueStatus, Watcher


class IssueCommentsApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='api-user')
        self.status, _ = IssueStatus.objects.get_or_create(
            slug='new',
            defaults={
                'name': 'New',
                'color': '#83eede',
                'is_closed': False,
                'order': 0,
            },
        )
        self.issue = Issue.objects.create(
            subject='Issue from API test',
            description='Issue body',
            status=self.status,
            created_by=self.user,
        )
        self.auth_headers = {'HTTP_AUTHORIZATION': self.user.profile.api_key}
        self.url = f'/api/issues/{self.issue.id}/comments/'

    def test_list_issue_comments(self):
        Comment.objects.create(issue=self.issue, author=self.user, text='First API comment')

        response = self.client.get(self.url, **self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['text'], 'First API comment')
        self.assertEqual(response.json()[0]['author']['username'], self.user.username)

    def test_create_issue_comment(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'text': 'Created from API'}),
            content_type='application/json',
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Comment.objects.filter(issue=self.issue, author=self.user, text='Created from API').exists())
        self.assertEqual(response.json()['issue_id'], self.issue.id)
        self.assertEqual(response.json()['author']['username'], self.user.username)
        self.assertTrue(
            IssueActivity.objects.filter(
                issue=self.issue,
                actor=self.user,
                action='added comment via API',
            ).exists()
        )

    def test_create_issue_comment_without_text_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json',
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('text', response.json())


class CommentDetailApiTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='comment-author')
        self.other_user = User.objects.create_user(username='other-user')
        self.status, _ = IssueStatus.objects.get_or_create(
            slug='new',
            defaults={
                'name': 'New',
                'color': '#83eede',
                'is_closed': False,
                'order': 0,
            },
        )
        self.issue = Issue.objects.create(
            subject='Issue from API test',
            description='Issue body',
            status=self.status,
            created_by=self.author,
        )
        self.comment = Comment.objects.create(
            issue=self.issue,
            author=self.author,
            text='Original API comment',
        )
        self.url = f'/api/comments/{self.comment.id}/'
        self.author_headers = {'HTTP_AUTHORIZATION': self.author.profile.api_key}
        self.other_headers = {'HTTP_AUTHORIZATION': self.other_user.profile.api_key}

    def test_update_comment_as_author(self):
        response = self.client.put(
            self.url,
            data=json.dumps({'text': 'Edited by author'}),
            content_type='application/json',
            **self.author_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, 'Edited by author')
        self.assertEqual(response.json()['text'], 'Edited by author')
        self.assertTrue(
            IssueActivity.objects.filter(
                issue=self.issue,
                actor=self.author,
                action='edited comment via API',
            ).exists()
        )

    def test_delete_comment_as_author(self):
        response = self.client.delete(self.url, **self.author_headers)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
        self.assertTrue(
            IssueActivity.objects.filter(
                issue=self.issue,
                actor=self.author,
                action='deleted comment via API',
            ).exists()
        )

    def test_update_comment_forbidden_for_non_author(self):
        response = self.client.put(
            self.url,
            data=json.dumps({'text': 'Edited by non-author'}),
            content_type='application/json',
            **self.other_headers,
        )

        self.assertEqual(response.status_code, 403)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, 'Original API comment')

    def test_delete_comment_forbidden_for_non_author(self):
        response = self.client.delete(self.url, **self.other_headers)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())


class WatchersAndActivitiesApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='issue-owner')
        self.watcher_user = User.objects.create_user(username='watcher-user')
        self.status, _ = IssueStatus.objects.get_or_create(
            slug='new',
            defaults={
                'name': 'New',
                'color': '#83eede',
                'is_closed': False,
                'order': 0,
            },
        )
        self.issue = Issue.objects.create(
            subject='Issue from API test',
            description='Issue body',
            status=self.status,
            created_by=self.owner,
        )
        self.auth_headers = {'HTTP_AUTHORIZATION': self.owner.profile.api_key}
        self.watchers_url = f'/api/issues/{self.issue.id}/watchers/'
        self.activities_url = f'/api/issues/{self.issue.id}/activities/'

    def test_add_and_list_watchers(self):
        add_response = self.client.post(
            self.watchers_url,
            data=json.dumps({'username': self.watcher_user.username}),
            content_type='application/json',
            **self.auth_headers,
        )

        self.assertEqual(add_response.status_code, 201)
        self.assertEqual(add_response.json()['username'], self.watcher_user.username)

        list_response = self.client.get(self.watchers_url, **self.auth_headers)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(list_response.json()[0]['username'], self.watcher_user.username)

    def test_remove_watcher(self):
        Watcher.objects.create(issue=self.issue, user=self.watcher_user)
        remove_url = f'/api/issues/{self.issue.id}/watchers/{self.watcher_user.username}/'

        response = self.client.delete(remove_url, **self.auth_headers)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Watcher.objects.filter(issue=self.issue, user=self.watcher_user).exists())

    def test_list_issue_activities(self):
        IssueActivity.objects.create(
            issue=self.issue,
            actor=self.owner,
            action='updated status via API',
            details='In progress',
        )

        response = self.client.get(self.activities_url, **self.auth_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['action'], 'updated status via API')
        self.assertEqual(response.json()[0]['actor']['username'], self.owner.username)


class IssueBulkInsertApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bulk-user')
        self.default_status, _ = IssueStatus.objects.get_or_create(
            slug='new',
            defaults={
                'name': 'New',
                'color': '#83eede',
                'is_closed': False,
                'order': 0,
            },
        )
        self.in_progress_status, _ = IssueStatus.objects.get_or_create(
            slug='in_progress',
            defaults={
                'name': 'In progress',
                'color': '#e2b93b',
                'is_closed': False,
                'order': 1,
            },
        )
        self.auth_headers = {'HTTP_AUTHORIZATION': self.user.profile.api_key}
        self.url = '/api/issues/bulk/'

    def test_bulk_insert_creates_multiple_issues(self):
        payload = {
            'issues_text': (
                'First issue | First description\n'
                'Second issue\n'
                '\n'
                '| should be ignored\n'
                'Third issue | Third description'
            ),
            'status_id': self.in_progress_status.id,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['created_count'], 3)
        self.assertEqual(len(body['issues']), 3)
        self.assertEqual(
            [item['subject'] for item in body['issues']],
            ['First issue', 'Second issue', 'Third issue'],
        )

        created_issues = Issue.objects.filter(created_by=self.user, status=self.in_progress_status)
        self.assertEqual(created_issues.count(), 3)
        self.assertEqual(
            IssueActivity.objects.filter(
                actor=self.user,
                action='created issue (bulk) via API',
            ).count(),
            3,
        )

    def test_bulk_insert_uses_default_status_when_missing(self):
        payload = {'issues_text': 'Single bulk issue | Description'}

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 201)
        issue = Issue.objects.get(subject='Single bulk issue', created_by=self.user)
        expected_default_status = IssueStatus.objects.order_by('order', 'name').first()
        self.assertEqual(issue.status, expected_default_status)

    def test_bulk_insert_rejects_invalid_status_id(self):
        payload = {'issues_text': 'Invalid status issue', 'status_id': 999999}

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('status_id', response.json())
        self.assertFalse(Issue.objects.filter(subject='Invalid status issue').exists())

    def test_bulk_insert_rejects_blank_issues_text(self):
        payload = {'issues_text': '   \n  '}

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            **self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('issues_text', response.json())
