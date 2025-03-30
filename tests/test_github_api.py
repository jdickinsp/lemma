from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from github import GithubException

from lemma.github_api import (
    BranchDiff,
    CommitDiff,
    GitHubAPI,
    GitHubDiffFetcher,
    GitHubRepoHelper,
    GitHubURLIdentifier,
    GitHubURLType,
    PullRequestDiff,
    fetch_git_diffs,
)


@pytest.fixture
def mock_github_api():
    with patch("lemma.github_api.GitHubAPI") as mock_api:
        # Configure the mock to return False for is_branch by default
        mock_api.return_value.is_branch.return_value = False
        yield mock_api.return_value


@pytest.fixture
def mock_repo():
    repo = Mock()
    repo.default_branch = "main"
    return repo


@pytest.fixture
def github_diff_fetcher(mock_github_api):
    return GitHubDiffFetcher(mock_github_api)


def test_identify_github_url_type(mock_github_api):
    cases = [
        ("https://github.com/owner/repo/tree/branch", GitHubURLType.BRANCH),
        ("https://github.com/owner/repo/tree/branch/folder", GitHubURLType.FOLDER_PATH),
        (
            "https://github.com/owner/repo/tree/branch/folder/subfolder",
            GitHubURLType.FOLDER_PATH,
        ),
        ("https://github.com/owner/repo/pull/123", GitHubURLType.PULL_REQUEST),
        ("https://github.com/owner/repo/pull/123/files", GitHubURLType.PULL_REQUEST),
        (
            "https://github.com/owner/repo/pull/123/commits/abcdef1234567890abcdef1234567890abcdef12",
            GitHubURLType.PULL_REQUEST_COMMIT,
        ),
        ("https://github.com/owner/repo/blob/branch/file.py", GitHubURLType.FILE_PATH),
        (
            "https://github.com/owner/repo/blob/branch/folder/file.py",
            GitHubURLType.FILE_PATH,
        ),
        (
            "https://github.com/owner/repo/commit/abcdef1234567890abcdef1234567890abcdef12",
            GitHubURLType.COMMIT,
        ),
        (
            "https://github.com/karpathy/llm.c/commit/8cf66fbb845665dabacba992e8a92631132a58d8",
            GitHubURLType.COMMIT,
        ),
        ("https://github.com", GitHubURLType.UNKNOWN),
        ("https://github.com/owner/repo", GitHubURLType.UNKNOWN),
    ]

    # Configure the mock to return True only for the specific 'branch' case
    mock_github_api.is_branch.side_effect = (
        lambda repo, ref, exact_match: ref == "branch"
    )

    for url, expected_type in cases:
        assert (
            GitHubURLIdentifier.identify_github_url_type(mock_github_api, url)
            == expected_type
        ), f"Failed for URL: {url}"


def test_extract_repo_and_pr_number():
    url = "https://github.com/owner/repo/pull/123"
    result = GitHubURLIdentifier.extract_repo_and_pr_number(url)
    assert result == {"pr_number": 123, "repo_name": "owner/repo"}

    invalid_url = "https://github.com/owner/repo"
    assert GitHubURLIdentifier.extract_repo_and_pr_number(invalid_url) is None


def test_extract_repo_and_commit_hash():
    result = GitHubURLIdentifier.extract_repo_and_commit_hash(
        "https://github.com/owner/repo/commit/1234567890abcdef1234567890abcdef12345678"
    )
    assert result == {
        "repo_name": "owner/repo",
        "commit_hash": "1234567890abcdef1234567890abcdef12345678",
    }


def test_extract_repo_and_commit_hash_invalid_url():
    result = GitHubURLIdentifier.extract_repo_and_commit_hash(
        "https://github.com/invalid/url"
    )
    assert result is None


def test_get_commit_hash_from_url():
    url = "https://github.com/owner/repo/pull/123/commits/1234567890abcdef1234567890abcdef12345678"
    result = GitHubURLIdentifier.get_commit_hash_from_url(url)
    assert result == {
        "repo_name": "owner/repo",
        "pr_number": "123",
        "commit_hash": "1234567890abcdef1234567890abcdef12345678",
    }


def test_get_commit_hash_from_url_invalid_url():
    result = GitHubURLIdentifier.get_commit_hash_from_url(
        "https://github.com/invalid/url"
    )
    assert result is None


def test_get_diff_header():
    file_mock = Mock()
    file_mock.filename = "test.py"
    file_mock.sha = "1234567890abcdef1234567890abcdef12345678"
    header = GitHubRepoHelper.get_diff_header(file_mock)
    assert header == (
        "diff --git a/test.py b/test.py\n"
        "index 1234567..1234567 100644\n"
        "--- a/test.py\n"
        "+++ b/test.py\n"
    )


def test_fetch_git_diffs_invalid_url():
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        fetch_git_diffs("https://invalid.url")


@patch("lemma.github_api.os.getenv")
def test_github_api_init(mock_getenv):
    mock_getenv.return_value = "fake_token"
    github_api = GitHubAPI("fake_token")
    assert github_api.github is not None


def test_get_github_pr_diff(github_diff_fetcher, mock_repo):
    mock_pr = Mock()
    mock_pr.head.sha = "abc123"
    mock_pr.body = "PR description"
    mock_pr.title = "PR title"
    mock_repo.get_pull.return_value = mock_pr

    mock_file = Mock()
    mock_file.filename = "test.py"
    mock_file.patch = "@@ -1,3 +1,3 @@\n-old line\n+new line"
    mock_pr.get_files.return_value = [mock_file]

    # Mock the get_repo method
    github_diff_fetcher.github_api.get_repo = Mock(return_value=mock_repo)

    # Mock the process_file method
    github_diff_fetcher.process_file = Mock(
        return_value={
            "filename": "test.py",
            "content": "file content",
            "patch": "@@ -1,3 +1,3 @@\n-old line\n+new line",
        }
    )

    result = github_diff_fetcher.get_github_pr_diff(1, "owner/repo")

    assert isinstance(result, PullRequestDiff)
    assert result.repo_name == "owner/repo"
    assert result.pr_number == 1
    assert result.title == "PR title"
    assert result.body == "PR description"
    assert result.file_names == ["test.py"]
    assert len(result.patches) == 1
    assert len(result.contents) == 1
    assert "@@ -1,3 +1,3 @@\n-old line\n+new line" in result.patches[0]
    assert result.contents[0] == "file content"

    # Verify that process_file was called with the correct arguments
    github_diff_fetcher.process_file.assert_called_once_with(
        mock_repo, mock_file, "abc123", False
    )


def test_get_github_pr_diff_not_found(github_diff_fetcher, mock_repo):
    # Mock the get_repo method
    github_diff_fetcher.github_api.get_repo = Mock(return_value=mock_repo)

    mock_repo.get_pull.side_effect = GithubException(404, "Not Found")

    with pytest.raises(GithubException):
        github_diff_fetcher.get_github_pr_diff(1, "owner/repo")

    # Verify that get_repo was called with the correct arguments
    github_diff_fetcher.github_api.get_repo.assert_called_once_with("owner/repo")


def test_get_github_commit_diff(github_diff_fetcher, mock_repo):
    mock_commit = Mock()
    mock_commit.sha = "abc123"
    mock_commit.commit.message = "Commit message"
    mock_repo.get_commit.return_value = mock_commit

    mock_file = Mock()
    mock_file.filename = "test.py"
    mock_file.patch = "@@ -1,3 +1,3 @@\n-old line\n+new line"
    mock_commit.files = [mock_file]

    github_diff_fetcher.github_api.get_repo = Mock(return_value=mock_repo)

    # Mock the process_file method instead of get_file_content
    github_diff_fetcher.process_file = Mock(
        return_value={
            "filename": "test.py",
            "content": "file content",
            "patch": "@@ -1,3 +1,3 @@\n-old line\n+new line",
        }
    )

    result = github_diff_fetcher.get_github_commit_diff("owner/repo", "abc123")

    assert isinstance(result, CommitDiff)
    assert result.repo_name == "owner/repo"
    assert result.commit_hash == "abc123"
    assert result.file_names == ["test.py"]
    assert len(result.patches) == 1
    assert len(result.contents) == 1
    assert "@@ -1,3 +1,3 @@\n-old line\n+new line" in result.patches[0]
    assert result.contents[0] == "file content"

    # Verify that process_file was called with the correct arguments
    github_diff_fetcher.process_file.assert_called_once_with(
        mock_repo, mock_file, "abc123", False
    )


def test_get_github_commit_diff_not_found(github_diff_fetcher, mock_repo):
    github_diff_fetcher.github_api.get_repo = Mock(return_value=mock_repo)
    mock_repo.get_commit.side_effect = GithubException(404, "Not Found")

    with pytest.raises(GithubException):
        github_diff_fetcher.get_github_commit_diff("owner/repo", "abc123")


def test_get_github_branch_diff(github_diff_fetcher, mock_repo):
    mock_comparison = Mock()
    mock_file = Mock()
    mock_file.filename = "test.py"
    mock_file.patch = "@@ -1,3 +1,3 @@\n-old line\n+new line"
    mock_comparison.files = [mock_file]
    mock_repo.compare.return_value = mock_comparison

    github_diff_fetcher.github_api.get_repo = Mock(return_value=mock_repo)

    # Mock the process_file method instead of get_file_content
    github_diff_fetcher.process_file = Mock(
        return_value={
            "filename": "test.py",
            "content": "file content",
            "patch": "@@ -1,3 +1,3 @@\n-old line\n+new line",
        }
    )

    result = github_diff_fetcher.get_github_branch_diff("owner/repo", "feature")

    assert isinstance(result, BranchDiff)
    assert result.repo_name == "owner/repo"
    assert result.compare_branch == "feature"
    assert result.base_branch == "main"  # Assuming 'main' is the default branch
    assert result.file_names == ["test.py"]
    assert len(result.patches) == 1
    assert len(result.contents) == 1
    assert "@@ -1,3 +1,3 @@\n-old line\n+new line" in result.patches[0]
    assert result.contents[0] == "file content"

    # Verify that process_file was called with the correct arguments
    github_diff_fetcher.process_file.assert_called_once_with(
        mock_repo, mock_file, "feature", False
    )

    # Verify that compare was called with the correct arguments
    mock_repo.compare.assert_called_once_with("main", "feature")


def test_get_github_branch_diff_not_found(github_diff_fetcher, mock_repo):
    github_diff_fetcher.github_api.get_repo = Mock(return_value=mock_repo)
    mock_repo.compare.side_effect = GithubException(404, "Not Found")

    with pytest.raises(GithubException):
        github_diff_fetcher.get_github_branch_diff("owner/repo", "feature")


def test_identify_github_url_type_with_query_params():
    assert (
        GitHubURLIdentifier.identify_github_url_type(
            mock_github_api, "https://github.com/owner/repo/pull/123?diff=split"
        )
        == GitHubURLType.PULL_REQUEST
    )
    assert (
        GitHubURLIdentifier.identify_github_url_type(
            mock_github_api,
            "https://github.com/owner/repo/commit/1234567890abcdef1234567890abcdef12345678?diff=split",
        )
        == GitHubURLType.COMMIT
    )


def test_identify_github_url_type_with_anchor():
    assert (
        GitHubURLIdentifier.identify_github_url_type(
            mock_github_api,
            "https://github.com/owner/repo/pull/123#discussion_r1234567890",
        )
        == GitHubURLType.PULL_REQUEST
    )
    assert (
        GitHubURLIdentifier.identify_github_url_type(
            mock_github_api,
            "https://github.com/owner/repo/commit/1234567890abcdef1234567890abcdef12345678#diff-1234567890abcdef1234567890abcdef12345678",
        )
        == GitHubURLType.COMMIT
    )


def test_extract_repo_and_pr_number_with_query_params():
    result = GitHubURLIdentifier.extract_repo_and_pr_number(
        "https://github.com/owner/repo/pull/123?diff=split"
    )
    assert result == {"pr_number": 123, "repo_name": "owner/repo"}


def test_extract_repo_and_commit_hash_with_query_params():
    result = GitHubURLIdentifier.extract_repo_and_commit_hash(
        "https://github.com/owner/repo/commit/1234567890abcdef1234567890abcdef12345678?diff=split"
    )
    assert result == {
        "repo_name": "owner/repo",
        "commit_hash": "1234567890abcdef1234567890abcdef12345678",
    }


@patch("lemma.github_api.GitHubDiffFetcher")
@patch("lemma.github_api.GitHubRepoHelper.get_github_info_from_url")
@patch("lemma.github_api.GitHubURLIdentifier.identify_github_url_type")
@patch("lemma.github_api.os.getenv")
def test_fetch_git_diffs_pull_request(
    mock_getenv, mock_identify_url_type, mock_get_github_info, mock_fetcher
):
    mock_getenv.return_value = "fake_token"
    mock_identify_url_type.return_value = GitHubURLType.PULL_REQUEST
    mock_get_github_info.return_value = {
        "owner": "owner",
        "repo": "repo",
        "pr_number": 123,
    }

    mock_fetcher_instance = mock_fetcher.return_value
    mock_fetcher_instance.get_github_pr_diff.return_value = PullRequestDiff(
        "owner/repo",
        123,
        "PR title",
        "PR description",
        ["file1.py"],
        ["patch1"],
        ["content1"],
    )

    result = fetch_git_diffs("https://github.com/owner/repo/pull/123")

    assert isinstance(result, PullRequestDiff)
    assert result.repo_name == "owner/repo"
    assert result.pr_number == 123
    assert result.title == "PR title"
    assert result.body == "PR description"
    assert result.file_names == ["file1.py"]
    assert result.patches == ["patch1"]
    assert result.contents == ["content1"]

    mock_identify_url_type.assert_called_once_with(
        ANY, "https://github.com/owner/repo/pull/123"
    )
    mock_get_github_info.assert_called_once_with(
        "https://github.com/owner/repo/pull/123", ANY, GitHubURLType.PULL_REQUEST
    )
    mock_fetcher_instance.get_github_pr_diff.assert_called_once_with(
        123, "owner/repo", ignore_tests=False
    )


def test_github_api_get_repo(mock_github_api):
    # Create a mock for the github attribute
    mock_github = Mock()
    mock_github.get_repo.return_value = "mock_repo"

    # Assign the mock to the github attribute of mock_github_api
    mock_github_api.github = mock_github

    # Configure the get_repo method on mock_github_api to use the underlying github.get_repo
    mock_github_api.get_repo = MagicMock(
        side_effect=lambda repo_name: mock_github.get_repo(repo_name)
    )

    # Now test the get_repo method
    assert mock_github_api.get_repo("owner/repo") == "mock_repo"

    # Verify that the underlying github.get_repo was called with the correct argument
    mock_github.get_repo.assert_called_once_with("owner/repo")


@pytest.fixture
def mock_diff_fetcher(mock_github_api):
    return GitHubDiffFetcher(mock_github_api)


def test_get_file_content(mock_diff_fetcher):
    mock_repo = Mock()
    mock_content = Mock()
    mock_content.encoding = "base64"
    mock_content.decoded_content = b"test content"
    mock_repo.get_contents.return_value = mock_content

    content = mock_diff_fetcher.get_file_content(mock_repo, "test.py", "main")
    assert content == "test content"

    # Test error handling
    mock_repo.get_contents.side_effect = Exception("API error")
    content = mock_diff_fetcher.get_file_content(mock_repo, "test.py", "main")
    assert content is None


# Add more tests for other methods in GitHubDiffFetcher


@patch("lemma.github_api.GitHubAPI")
@patch("lemma.github_api.GitHubDiffFetcher")
@patch("lemma.github_api.GitHubRepoHelper.get_github_info_from_url")
@patch("lemma.github_api.GitHubURLIdentifier.identify_github_url_type")
@patch("lemma.github_api.GitHubURLIdentifier.extract_repo_and_commit_hash")
@patch("lemma.github_api.GitHubURLIdentifier.extract_repo_and_pr_number")
def test_fetch_git_diffs(
    mock_extract_pr,
    mock_extract_commit,
    mock_identify_url_type,
    mock_get_github_info,
    mock_fetcher_class,
    mock_api_class,
):
    mock_fetcher = mock_fetcher_class.return_value

    # Test PR URL
    pr_url = "https://github.com/owner/repo/pull/123"
    mock_identify_url_type.return_value = GitHubURLType.PULL_REQUEST
    mock_get_github_info.return_value = {
        "owner": "owner",
        "repo": "repo",
        "repo_name": "owner/repo",
        "pr_number": "123",
    }
    mock_fetcher.get_github_pr_diff.return_value = "pr_diff"
    result = fetch_git_diffs(pr_url)
    assert result == "pr_diff"

    # Test branch URL
    branch_url = "https://github.com/owner/repo/tree/branch"
    mock_identify_url_type.return_value = GitHubURLType.BRANCH
    mock_get_github_info.return_value = {
        "owner": "owner",
        "repo": "repo",
        "repo_name": "owner/repo",
        "branch": "branch",
    }
    mock_fetcher.get_github_branch_diff.return_value = "branch_diff"
    result = fetch_git_diffs(branch_url)
    assert result == "branch_diff"

    # Test commit URL
    commit_url = "https://github.com/owner/repo/commit/abcdef1234567890"
    mock_identify_url_type.return_value = GitHubURLType.COMMIT
    mock_extract_commit.return_value = {
        "repo_name": "owner/repo",
        "commit_hash": "abcdef1234567890",
    }
    mock_get_github_info.return_value = {
        "owner": "owner",
        "repo": "repo",
        "repo_name": "owner/repo",
        "commit_hash": "abcdef1234567890",
    }
    mock_fetcher.get_github_commit_diff.return_value = "commit_diff"
    result = fetch_git_diffs(commit_url)
    assert result == "commit_diff"

    # Test invalid commit URL
    invalid_commit_url = "https://github.com/owner/repo/commit/invalid"
    mock_identify_url_type.return_value = GitHubURLType.COMMIT
    mock_extract_commit.return_value = None
    with pytest.raises(ValueError, match="Invalid Commit URL"):
        fetch_git_diffs(invalid_commit_url)

    # Test file URL
    file_url = "https://github.com/owner/repo/blob/branch/file.py"
    mock_identify_url_type.return_value = GitHubURLType.FILE_PATH
    mock_get_github_info.return_value = {
        "owner": "owner",
        "repo": "repo",
        "repo_name": "owner/repo",
        "branch": "branch",
        "file_path": "file.py",
    }
    mock_fetcher.get_github_file_content.return_value = "file_content"
    result = fetch_git_diffs(file_url)
    assert result == "file_content"

    # Test folder URL
    folder_url = "https://github.com/owner/repo/tree/branch/folder"
    mock_identify_url_type.return_value = GitHubURLType.FOLDER_PATH
    mock_get_github_info.return_value = {
        "owner": "owner",
        "repo": "repo",
        "repo_name": "owner/repo",
        "branch": "branch",
        "folder_path": "folder",
    }
    mock_fetcher.get_github_folder_contents.return_value = "folder_contents"
    result = fetch_git_diffs(folder_url)
    assert result == "folder_contents"

    # Test invalid URL
    invalid_url = "https://invalid-url.com"
    mock_identify_url_type.return_value = GitHubURLType.UNKNOWN
    with pytest.raises(ValueError):
        fetch_git_diffs(invalid_url)

    # Test missing GitHub token
    with patch("os.getenv", return_value=None):
        with pytest.raises(ValueError):
            fetch_git_diffs(pr_url)
