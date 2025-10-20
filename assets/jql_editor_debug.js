/**
 * Debug script to diagnose JQL editor initialization issues
 * Run this in browser console to check editor state
 */

(function () {
  console.log("=== JQL Editor Debug Info ===");

  // Check for containers
  const containers = document.querySelectorAll(".jql-editor-container");
  console.log(`Found ${containers.length} .jql-editor-container elements`);

  containers.forEach((container, index) => {
    console.log(`\nContainer ${index + 1}:`);
    console.log("  ID:", container.id);
    console.log("  Children count:", container.children.length);
    console.log("  innerHTML length:", container.innerHTML.length);
    console.log(
      "  Has textarea child:",
      container.querySelector("textarea") !== null
    );

    // Check for textarea
    const textarea = container.querySelector("textarea");
    if (textarea) {
      console.log("  Textarea found:");
      console.log("    ID:", textarea.id);
      console.log("    Class:", textarea.className);
      console.log("    ReadOnly:", textarea.readOnly);
      console.log("    Disabled:", textarea.disabled);
      console.log("    Value:", textarea.value.substring(0, 50));
      console.log("    Placeholder:", textarea.placeholder);
    } else {
      console.log("  NO TEXTAREA FOUND IN CONTAINER!");
    }
  });

  // Check for Store elements
  const stores = document.querySelectorAll('[id="jira-jql-query"]');
  console.log(`\nFound ${stores.length} elements with id="jira-jql-query"`);

  // Check for hidden textarea
  const hiddenTextarea = document.getElementById("jira-jql-query-hidden");
  if (hiddenTextarea) {
    console.log("\nHidden textarea found:");
    console.log(
      "  Display style:",
      window.getComputedStyle(hiddenTextarea).display
    );
    console.log("  ReadOnly:", hiddenTextarea.readOnly);
    console.log("  Disabled:", hiddenTextarea.disabled);
  } else {
    console.log("\nHidden textarea NOT found");
  }

  // Check initialization
  console.log(
    "\nScript loaded:",
    typeof window.initializeJQLEditors !== "undefined"
  );
  console.log(
    "jqlLanguageMode loaded:",
    typeof window.jqlLanguageMode !== "undefined"
  );

  console.log("\n=== End Debug Info ===");
})();
