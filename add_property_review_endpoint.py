# Add this to api.py after the nearby-amenities endpoint

@app.post("/api/property-review")
async def get_property_review(request: dict):
    """
    Get or generate AI review for a property using Perplexity API
    
    Flow:
    1. Check if Property_Review exists in database
    2. If exists: return from database
    3. If not: call Perplexity API to generate review
    4. Save review to database
    5. Return review
    """
    property_id = request.get('property_id')
    project_name = request.get('project_name', '')
    builder_name = request.get('builder_name', '')
    area_name = request.get('area_name', '')
    
    if not property_id:
        return {"error": "property_id is required"}
    
    print(f"\n📝 Fetching review for property {property_id}: {project_name}")
    
    try:
        supabase = get_supabase()
        
        # Check if review already exists in database
        result = supabase.table('unified_data_DataType_Raghu').select('Property_Review').eq('id', property_id).execute()
        
        if result.data and len(result.data) > 0:
            existing_review = result.data[0].get('Property_Review')
            
            if existing_review and existing_review.strip():
                print(f"✅ Found existing review in database")
                return {
                    "success": True,
                    "review": existing_review,
                    "source": "database",
                    "property_id": property_id
                }
        
        # No review exists - generate using Perplexity API
        print(f"🤖 Generating new review using Perplexity AI...")
        
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not perplexity_api_key:
            return {"error": "Perplexity API key not configured", "success": False}
        
        # Construct search query for Perplexity
        search_query = f"Find and summarize real user reviews and feedback about {project_name} by {builder_name} in {area_name}. Include pros, cons, and overall sentiment from actual buyers and residents."
        
        # Call Perplexity API
        perplexity_url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",  # Online model for web search
            "messages": [
                {
                    "role": "system",
                    "content": "You are a real estate analyst. Provide concise, factual summaries of property reviews based on online sources. Keep responses under 150 words."
                },
                {
                    "role": "user",
                    "content": search_query
                }
            ],
            "max_tokens": 300,
            "temperature": 0.2,
            "top_p": 0.9
        }
        
        response = requests.post(perplexity_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'choices' in data and len(data['choices']) > 0:
            review_text = data['choices'][0]['message']['content']
            
            print(f"✅ Generated review: {review_text[:100]}...")
            
            # Save review to database
            update_result = supabase.table('unified_data_DataType_Raghu').update({
                'Property_Review': review_text
            }).eq('id', property_id).execute()
            
            print(f"💾 Saved review to database")
            
            return {
                "success": True,
                "review": review_text,
                "source": "perplexity_api",
                "property_id": property_id
            }
        else:
            return {"error": "No response from Perplexity API", "success": False}
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Perplexity API timeout")
        return {"error": "AI service timeout - please try again", "success": False}
    except requests.exceptions.RequestException as e:
        print(f"❌ Perplexity API error: {e}")
        return {"error": f"AI service error: {str(e)}", "success": False}
    except Exception as e:
        print(f"❌ Error generating review: {e}")
        return {"error": str(e), "success": False}
