import ReactMarkdown from 'react-markdown';

const TestMarkdown = () => {
  const testMarkdown = `
# Test Markdown Rendering

This is a test of markdown rendering with images.

## Sample Image
![Test Image](https://via.placeholder.com/300x200/4CAF50/FFFFFF?text=Test+Image)

**Bold text** and *italic text* should render properly.

### List of items:
1. First item
2. Second item
3. Third item

[Link to example](https://example.com)

> This is a blockquote for testing.
  `;

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Markdown Rendering Test</h1>
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="text-sm text-green-800 prose prose-sm max-w-none
          prose-headings:text-green-900 prose-headings:font-medium
          prose-p:text-green-800 prose-p:leading-relaxed
          prose-strong:text-green-900 prose-strong:font-semibold
          prose-img:rounded-lg prose-img:shadow-sm prose-img:max-w-full prose-img:h-auto
          prose-a:text-green-700 prose-a:underline
          prose-ul:text-green-800 prose-ol:text-green-800
          prose-li:text-green-800">
          <ReactMarkdown>{testMarkdown}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

export default TestMarkdown; 