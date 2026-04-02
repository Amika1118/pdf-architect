from pdf_architect.core.converter import ImageToPdfConverter

converter = ImageToPdfConverter(
    input_folder="examples",          # folder with images
    output_folder="./pdfs",           # output directory
    batch_mode=True,
    batch_size=200,
    num_threads=10,
    use_webp=True,
    keep_webp=False,
    recursive=False
)
converter.run()