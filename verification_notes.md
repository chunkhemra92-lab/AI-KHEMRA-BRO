# Verification Notes — v6.4

## Static rule tests

The rule test suite passed. It verified that the Khmer-output filter accepts Khmer script and rejects English, Chinese, Korean, Thai, and Vietnamese/Latin text. It also verified canonical conversion to the four permitted tags (`M`, `F`, `M_THINK`, and `F_THINK`), the presence of all six translation rules in the generated prompt, valid SRT construction, and rejection of non-Khmer output.

## Startup check

The Streamlit v6.4 application started as a fresh process on local port 8503. A new browser session reached the private customer login page without an import or startup exception. No customer or administrator credential was entered, so protected workflow features were not exercised in the browser.

## Updated language filter check

The rule suite was rerun after extending the forbidden-script matcher for Latin Extended characters used in Vietnamese. The suite passed again, confirming that a standalone Vietnamese character such as `đ` is rejected alongside English, Chinese, Korean, Thai, and Japanese text.

## Reload check

After the final code changes, the running Streamlit process was loaded again in the browser and rendered the customer login screen normally. No startup or import exception appeared during the reload check.
