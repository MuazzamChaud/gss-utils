Feature: Decouple external resources
  As a data engineer, when developing an automated pipeline,
  I want to keep a local cache of the web resources I fetch,
  so that I can use these as test fixtures to test my pipeline against.

  Scenario: first time scrape
    Given the 'RECORD_MODE' environment variable is 'new_episodes'
    And the fixtures directory is empty
    And I directly scrape the page "https://www.ons.gov.uk/economy/nationalaccounts/uksectoraccounts/datasets/unitedkingdomeconomicaccountsbalanceofpaymentscurrentaccount"
    Then the fixtures directory has a file "recording.yml"

  Scenario: next time scrape
    Given the 'RECORD_MODE' environment variable is 'none'
    And the fixtures directory has a file "recording.yml"
    And I directly scrape the page "https://www.ons.gov.uk/economy/nationalaccounts/uksectoraccounts/datasets/unitedkingdomeconomicaccountsbalanceofpaymentscurrentaccount"
    Then the fixtures file "recording.yml" should not change

  Scenario: record distribution
    Given the 'RECORD_MODE' environment variable is 'new_episodes'
    And the fixtures directory is empty
    And I directly scrape the page "https://www.ons.gov.uk/economy/nationalaccounts/uksectoraccounts/datasets/unitedkingdomeconomicaccountsbalanceofpaymentscurrentaccount"
    And select the distribution whose title starts with "UK Economic Accounts: balance of payments"
    And directly fetch the distribution as a databaker object
    Then the fixtures directory has a file "recording.yml"

  Scenario: playback distribution
    Given the 'RECORD_MODE' environment variable is 'none'
    And the fixtures directory has a file "recording.yml"
    And I directly scrape the page "https://www.ons.gov.uk/economy/nationalaccounts/uksectoraccounts/datasets/unitedkingdomeconomicaccountsbalanceofpaymentscurrentaccount"
    And select the distribution whose title starts with "UK Economic Accounts: balance of payments"
    And directly fetch the distribution as a databaker object
    Then the fixtures file "recording.yml" should not change
