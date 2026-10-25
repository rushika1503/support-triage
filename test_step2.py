from redact import find_emails

assert find_emails("Mail me at jo.lee@contoso.com for details") == ["jo.lee@contoso.com"]
assert find_emails("Contact priya@example.com.") == ["priya@example.com"]
assert find_emails("No email here") == []
assert find_emails("Write to a.kim@example.com or sam@fabrikam.com") == ["a.kim@example.com", "sam@fabrikam.com"]
print("all passed")