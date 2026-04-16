from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Attachment, Comment, Issue, IssueActivity, IssueStatus


class IssueFeatureTests(TestCase):
	def setUp(self):
		self.creator = User.objects.create_user(username='creator')
		self.assignee = User.objects.create_user(username='assignee')
		self.other_user = User.objects.create_user(username='other-user')
		self.client.force_login(self.creator)
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
		self.assertIn('evidence', attachment.file.name)

		detail_response = self.client.get(reverse('issue_detail', args=[self.issue.id]))
		self.assertContains(detail_response, 'evidence')

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
				'status': self.status.id,
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

	def test_issue_delete_forbidden_for_non_creator(self):
		self.client.force_login(self.other_user)

		response = self.client.post(
			reverse('issue_delete', args=[self.issue.id]),
		)

		self.assertEqual(response.status_code, 403)
		self.assertTrue(Issue.objects.filter(id=self.issue.id).exists())

	def test_attachment_delete_forbidden_for_non_uploader(self):
		upload = SimpleUploadedFile('evidence.txt', b'test attachment content')
		attachment = Attachment.objects.create(
			issue=self.issue,
			uploaded_by=self.creator,
			file=upload,
		)
		self.client.force_login(self.other_user)

		response = self.client.post(
			reverse('attachment_delete', args=[self.issue.id, attachment.id]),
		)

		self.assertEqual(response.status_code, 403)
		self.assertTrue(Attachment.objects.filter(id=attachment.id).exists())

	def test_comment_edit_forbidden_for_non_author(self):
		comment = Comment.objects.create(
			issue=self.issue,
			author=self.creator,
			text='Original text',
		)
		self.client.force_login(self.other_user)

		response = self.client.post(
			reverse('comment_edit', args=[comment.id]),
			{'text': 'Updated by non-author'},
		)

		self.assertEqual(response.status_code, 403)
		comment.refresh_from_db()
		self.assertEqual(comment.text, 'Original text')

	def test_comment_delete_forbidden_for_non_author(self):
		comment = Comment.objects.create(
			issue=self.issue,
			author=self.creator,
			text='Comment to keep',
		)
		self.client.force_login(self.other_user)

		response = self.client.post(
			reverse('comment_delete', args=[comment.id]),
		)

		self.assertEqual(response.status_code, 403)
		self.assertTrue(Comment.objects.filter(id=comment.id).exists())

	def test_issue_edit_forbidden_for_non_creator(self):
		self.client.force_login(self.other_user)

		response = self.client.post(
			reverse('issue_edit', args=[self.issue.id]),
			{
				'subject': 'Hacked subject',
				'description': 'Hacked description',
				'status': self.status.id,
				'assigned_to': self.assignee.id,
			},
		)

		self.assertEqual(response.status_code, 403)
		self.issue.refresh_from_db()
		self.assertEqual(self.issue.subject, 'Sample issue')

	def test_issue_edit_updates_fields_for_creator(self):
		response = self.client.post(
			reverse('issue_edit', args=[self.issue.id]),
			{
				'subject': 'Edited issue',
				'description': 'Edited description',
				'status': self.status.id,
				'assigned_to': self.assignee.id,
			},
		)

		self.assertEqual(response.status_code, 302)
		self.issue.refresh_from_db()
		self.assertEqual(self.issue.subject, 'Edited issue')
		self.assertEqual(self.issue.description, 'Edited description')
		self.assertEqual(self.issue.assigned_to, self.assignee)

	def test_bulk_insert_creates_multiple_issues(self):
		response = self.client.post(
			reverse('issue_bulk_insert'),
			{
				'issues_text': 'Bulk one | First description\nBulk two\n\nBulk three | Third description',
				'status': self.status.id,
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertTrue(Issue.objects.filter(subject='Bulk one').exists())
		self.assertTrue(Issue.objects.filter(subject='Bulk two').exists())
		self.assertTrue(Issue.objects.filter(subject='Bulk three').exists())

	def test_issue_detail_lists_activities(self):
		IssueActivity.objects.create(
			issue=self.issue,
			actor=self.creator,
			action='created issue',
			details='Sample issue',
		)

		response = self.client.get(reverse('issue_detail', args=[self.issue.id]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'created issue')
