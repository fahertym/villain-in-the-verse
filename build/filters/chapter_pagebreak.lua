-- Insert a page break before each level-2 header, so chapters start on a new page
-- Works across PDF (LaTeX), EPUB (CSS page-break), and DOCX

local function pagebreak_block()
  if FORMAT:match('latex') then
    return pandoc.RawBlock('latex', '\\clearpage')
  elseif FORMAT:match('epub') or FORMAT:match('html') then
    -- epub/html: use a div with CSS page-break
    return pandoc.Div({}, pandoc.Attr('', { 'pagebreak' }))
  elseif FORMAT:match('docx') then
    return pandoc.RawBlock('openxml',
      '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
  else
    -- Fallback: a horizontal rule as a visible separator
    return pandoc.HorizontalRule()
  end
end

-- Track if we've seen the first header (title page)
local seen_first_header = false

function Header(el)
  -- Chapters are level-2 headings (## ...)
  if el.level == 2 then
    -- Don't add page break for the subtitle on title page
    if not seen_first_header then
      seen_first_header = true
      return nil  -- No page break for title page subtitle
    end
    -- Add page break before all other level-2 headers (chapters)
    return { pagebreak_block(), el }
  elseif el.level == 1 then
    seen_first_header = true
    return nil  -- No modification to level-1 headers
  end
  return nil
end