# Base lab content skeleton

This repo contains a skeleton for lab content. You can fork and use it as a baseline for a new lab.

## How to import in bakery

For the time being Hermione is supporting repos from:

- GitHub
- BitBucket

to push the content in Bakery you have to call Hermione, our import service, with a webhook,
specifying the vendor of the repos adding the access token to authenticate the request.

    https://cloudacademy.com/webhooks/hermione/{VENDOR}/?access_token={ACCESS_TOKEN}

### When content is imported on bakery

The content will be imported only when a new tag is pushed:

    git tag v1.0.0
    git push --tags

### Vendor values:

- github
- bitbucket

### Access token

For the time being you've to ask the lab team for it.

### Stage

If you want to test the content on stage, just point the webhook to stage:


    https://stage.cloudacademy.com/webhooks/hermione/{VENDOR}/?access_token={ACCESS_TOKEN}

### MarkDown version

At the moment is fully supported GitHub Flavored Markdown Spec

   https://github.github.com/gfm/

Under the hood HTML rendering is handled by Python-Markdown with some extension:

   https://python-markdown.github.io/

Thanks to its modularity we could add extensions to handle new cases or custom behaviour.

For example, automatic upload to S3 of the assets is managed by a custom extension.


## Repo structure


```
   .
   +-- config.yaml
   +-- description.md
   +-- metadata.yaml
   +-- assets
   |   # all assets contained in the lab description
   |   [...]
   +-- steps
   |   +-- 1_lab_step_example
   |   |   +-- assets
   |   |   # all assets contained in the lab step
   |   |   [...]
   |   |   +-- checks
   |   |   |   +-- 1_vcf_example
   |   |   |   |   +-- config.yaml
   |   |   |   |   +-- description.md
   |   |   |   |   +-- source.py
   |   |   |   # all checks order by filesystem
   |   |   |   [...]
   |   |   +-- config.yaml
   |   |   +-- description.md
   |   |   +-- documentation.md
   |   # all steps order by filesystem
   |   [...]
   +-- environments
   |   +-- 1_env_example
   |   |   +-- config.yaml
   |   |   +-- template.yaml
   |   |   +-- security_policy
   |   |   |   +-- config.yaml
   |   |   |   +-- policy_body.yaml
   |   # all environments order by filesystem
   |   [...]

```

## Markdown Syntax Examples

### Test Lab Content

test description with GitHub Flavored Markdown

![](assets/image1.jpg)

- George Washington
- John Adams
- Thomas Jefferson

* George Washington
* John Adams
* Thomas Jefferson


| Syntax      | Description |
| ----------- | ----------- |
| Header      | Title       |
| Paragraph   | Text        |

``` js
var foo = function (bar) {
  return bar++;
};

console.log(foo(5));
```


- [ ] foo
- [x] bar

Visit www.commonmark.org.

~~Hi~~ Hello, world!

<ins>underline</ins> is accomplished with `ins` html tags

paragraph

    code
