#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import check_jira


# In[ ]:


jira = check_jira.create_jira()


# In[ ]:


j_issue=jira.create_issue(project='TSP', 
                          summary='test python jira API', 
                          description='test JIRA api',
                         issuetype={'name': 'Task'})


# In[ ]:


j_issue.key


# In[ ]:


comment = jira.add_comment(j_issue.key, 'new comment')


# In[ ]:


from io import StringIO
attachment = StringIO()
attachment.write('some data')
jira.add_attachment(issue=j_issue, attachment=attachment, filename='content.txt')


# In[ ]:


j_issue.update()


# In[ ]:


for attachment in j_issue.fields.attachment:
    print("Name: '{filename}', size: {size}".format(
        filename=attachment.filename, size=attachment.size))


# In[ ]:


j_issue.fields.attachment


# In[ ]:


for c in j_issue.fields.comment.comments:
    print(c)


# In[ ]:


for a in j_issue.fields.attachment:
    print(a)


# In[ ]:


print(j_issue.fields.attachment[0].id)


# In[ ]:


for attachment in j_issue.fields.attachment:
    print("Id '{id}, Name: '{filename}', size: {size}".format(
        id=attachment.id, filename=attachment.filename, size=attachment.size))


# In[ ]:


jira.delete_attachment(j_issue.fields.attachment[0].id)


# In[ ]:


j_issue.update()


# In[ ]:


for c in j_issue.fields.comment.comments:
    print(c)


# In[ ]:


for a in j_issue.fields.attachment:
    print(a)


# In[ ]:


j_issue.id


# ### Check transitions

# In[ ]:


jira.transitions(j_issue.id)


# In[ ]:


jira.transition_issue(j_issue.key, '31')


# In[ ]:


j_issue.key


# In[ ]:


jira.transition_issue(j_issue.key, '11')


# In[ ]:


j_issue=jira.issue('TSP-22')


# In[ ]:


jira.transitions(j_issue.id)


# In[ ]:


j_issue.fields.status


# In[ ]:


j_issue.key


# In[ ]:


jira.transition_issue('TSP-22', 'In Progress')


# In[ ]:


for j in jira.search_issues('project = TSP AND text ~ RM'):
    print(j.key)
    j.update(summary=j.fields.summary.replace(r'OLD:[RM:', '[OLD-RM'))


# In[1]:


import check_redmine


# In[2]:


redmine_lib, redmine_iss = check_redmine.create_redmine()


# In[7]:


count = 0
for r in redmine_lib.issue.filter(status='Open'):
    print(r.id)
    count+=1
print(count)


# In[ ]:




