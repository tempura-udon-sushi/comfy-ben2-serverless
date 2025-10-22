Here's a step-by-step guide on how to use Qwen3-VL gguf locally on your CPU, based on the provided video [[00:36](http://www.youtube.com/watch?v=Uvcy8V6quok&t=36)]:

*could use Q5 model as well:
https://huggingface.co/NexaAI/Qwen3-VL-4B-Thinking-GGUF/tree/main


---

## 💻 Running Qwen3-VL 30B on CPU Locally

This process leverages `llama.cpp`, an inference engine designed to run models on CPU and other backends [[00:51](http://www.youtube.com/watch?v=Uvcy8V6quok&t=51)]. While it allows you to run the model without a GPU, keep in mind that performance will be slower and there may be some accuracy tradeoffs due to the 4-bit quantization of this Mixture-of-Experts (MoE) model [[00:44](http://www.youtube.com/watch?v=Uvcy8V6quok&t=44)], [[03:55](http://www.youtube.com/watch?v=Uvcy8V6quok&t=235)].

### Prerequisites
* **Decent Modern CPU:** You'll need a relatively recent CPU.
* **RAM:** Approximately 16GB to 32GB of RAM is recommended [[00:44](http://www.youtube.com/watch?v=Uvcy8V6quok&t=44)].
* **Ubuntu System:** The demonstration in the video uses an Ubuntu system [[01:34](http://www.youtube.com/watch?v=Uvcy8V6quok&t=94)].

---

### Step-by-Step Instructions

#### Step 1: Clone the `llama.cpp` Repository
First, you need to clone the `llama.cpp` repository to your local system [[01:55](http://www.youtube.com/watch?v=Uvcy8V6quok&t=115)].

#### Step 2: Build `llama.cpp`
After cloning, navigate to the `llama.cpp` directory and build the project. This step will take some time to complete [[02:00](http://www.youtube.com/watch?v=Uvcy8V6quok&t=120)].

#### Step 3: Patch `llama.cpp` for Qwen3-VL
To run Qwen3-VL, you need to patch `llama.cpp`.
1.  Go to the `llama.cpp` directory you cloned [[02:24](http://www.youtube.com/watch?v=Uvcy8V6quok&t=144)].
2.  Visit the Hugging Face model card for the Qwen3-VL gguf quantized version (the link is usually provided in the video description) [[02:33](http://www.youtube.com/watch?v=Uvcy8V6quok&t=153)].
3.  In the "Files" section, download the patch file (a small file, around 28.8 KB) [[02:38](http://www.youtube.com/watch?v=Uvcy8V6quok&t=158)]. Save this file within your `llama.cpp` directory [[02:46](http://www.youtube.com/watch?v=Uvcy8V6quok&t=166)].
4.  Once the patch file is downloaded, run the `git apply` command with the patch file name in your terminal [[03:06](http://www.youtube.com/watch?v=Uvcy8V6quok&t=186)]. A lack of output indicates a successful application of the patch [[03:14](http://www.youtube.com/watch?v=Uvcy8V6quok&t=194)].

#### Step 4: Download the Model Files
From the same Hugging Face model card:
1.  Download the main **GGUF model file** (e.g., `Qwen3-VL-30B.gguf`) [[03:22](http://www.youtube.com/watch?v=Uvcy8V6quok&t=202)]. This file contains the weights, vocabulary, and metadata [[03:32](http://www.youtube.com/watch?v=Uvcy8V6quok&t=212)].
2.  Download the **`mmproj` file** (e.g., `mmproj-model-qwen3-vl-30b.gguf`) [[03:28](http://www.youtube.com/watch?v=Uvcy8V6quok&t=208)], [[04:23](http://www.youtube.com/watch?v=Uvcy8V6quok&t=263)]. This multimodal projector file is crucial for combining text with images and aligning image embeddings for text reasoning [[04:34](http://www.youtube.com/watch?v=Uvcy8V6quok&t=274)], [[04:44](http://www.youtube.com/watch?v=Uvcy8V6quok&t=284)]. Without it, the vision model cannot function correctly [[04:51](http://www.youtube.com/watch?v=Uvcy8V6quok&t=291)].
3.  It's recommended to save both these files in the `llama.cpp/models` directory, though you can choose another location [[05:01](http://www.youtube.com/watch?v=Uvcy8V6quok&t=301)].

#### Step 5: Run the Model
Once both files are downloaded, you can run the model using the `llama.cpp` command-line interface (CLI). The video demonstrates running a command that includes specifying the CPU backend, the GGUF model file, the `mmproj` file, and the image you want the model to describe [[05:46](http://www.youtube.com/watch?v=Uvcy8V6quok&t=346)]. For example, the video uses an image of channel members and asks the model to describe it [[05:53](http://www.youtube.com/watch?v=Uvcy8V6quok&t=353)].

#### Optional: GPU Offloading
If you have a GPU and want to take advantage of it for faster inference, you can change the `NGL` parameter (likely `ngl` or `n_gpu_layers`) in your command to a high number (e.g., `99`) to offload layers to the GPU [[07:53](http://www.youtube.com/watch?v=Uvcy8V6quok&t=473)]. Otherwise, ensure it's set to prevent GPU usage if you strictly want CPU-only operation [[06:54](http://www.youtube.com/watch?v=Uvcy8V6quok&t=414)].

---
Video Source: [Run Qwen3-VL 30B on CPU Locally for Images and Videos - No GPU Needed](https://www.youtube.com/watch?v=Uvcy8V6quok)
http://googleusercontent.com/youtube_content/0