from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Attachment, Comment, Issue, IssueStatus


class IssueFeatureTests(TestCase):
	def setUp(self):
		self.creator = User.objects.create_user(username='creator')
		self.assignee = User.objects.create_user(username='assignee')
		self.client.force_login(self.creator)
		self.status = IssueStatus.objects.create(
			name='New',
			slug='new',
			color='#83eede',
			is_closed=False,
			order=0,
		)
		self.issue = Issue.objects.create(
			subject='Sample issue',
			description='Sample description',
			created_by=self.creator,
			assigned_to=self.creator,
			status=self.status,
		)

	def test_assign_issue(self):
		response = self.client.post(
			reverse('issue_assign', args=[self.issue.id]),
			{'assigned_to': self.assignee.id},
		)

		self.assertEqual(response.status_code, 302)
		self.issue.refresh_from_db()
		self.assertEqual(self.issue.assigned_to, self.assignee)

	def test_add_and_delete_attachment(self):
		upload = SimpleUploadedFile('evidence.txt', b'test attachment content')

		add_response = self.client.post(
			reverse('attachment_add', args=[self.issue.id]),
			{'file': upload},
		)

		self.assertEqual(add_response.status_code, 302)
		attachment = Attachment.objects.get(issue=self.issue)
		self.assertTrue(attachment.file.name.endswith('evidence.txt'))

		detail_response = self.client.get(reverse('issue_detail', args=[self.issue.id]))
		self.assertContains(detail_response, 'evidence.txt')

		delete_response = self.client.post(
			reverse('attachment_delete', args=[self.issue.id, attachment.id]),
		)
		self.assertEqual(delete_response.status_code, 302)
		self.assertFalse(Attachment.objects.filter(id=attachment.id).exists())

	def test_comments_are_listed_in_detail(self):
		Comment.objects.create(
			issue=self.issue,
			author=self.creator,
			text='This is a comment in the issue.',
		)

		response = self.client.get(reverse('issue_detail', args=[self.issue.id]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'This is a comment in the issue.')

	def test_create_issue_from_new_view(self):
		response = self.client.post(
			reverse('issue_new'),
			{
				'subject': 'Created from test',
				'description': 'Issue body',
				'assigned_to': self.assignee.id,
				'status': self.status,
			},
		)

		self.assertEqual(response.status_code, 302)
		created_issue = Issue.objects.get(subject='Created from test')
		self.assertEqual(created_issue.description, 'Issue body')
		self.assertEqual(created_issue.created_by, self.creator)
		self.assertEqual(created_issue.assigned_to, self.assignee)

	def test_add_comment(self):
		response = self.client.post(
			reverse('comment_add', args=[self.issue.id]),
			{'text': 'New comment from test'},
		)

		self.assertEqual(response.status_code, 302)
		comment = Comment.objects.get(issue=self.issue, text='New comment from test')
		self.assertEqual(comment.author, self.creator)

	def test_edit_comment(self):
		comment = Comment.objects.create(
			issue=self.issue,
			author=self.creator,
			text='Original text',
		)

		response = self.client.post(
			reverse('comment_edit', args=[comment.id]),
			{'text': 'Updated text'},
		)

		self.assertEqual(response.status_code, 302)
		comment.refresh_from_db()
		self.assertEqual(comment.text, 'Updated text')

	def test_delete_comment(self):
		comment = Comment.objects.create(
			issue=self.issue,
			author=self.creator,
			text='Comment to delete',
		)

		response = self.client.post(
			reverse('comment_delete', args=[comment.id]),
		)

		self.assertEqual(response.status_code, 302)
		self.assertFalse(Comment.objects.filter(id=comment.id).exists())
